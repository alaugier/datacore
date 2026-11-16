"""DAG Airflow orchestrant le pipeline DATA CORE (issue #100, stretch goal).

Perimetre strict (voir issue #100 et chapitre 5 du rapport, "Pourquoi
pas un orchestrateur") : appelle les scripts/CLI deja existants et deja
documentes (chapitre 5 §6.5, "Rejouer le remplissage des donnees et les
pipelines") tels quels, sans reecrire la moindre logique metier. Ce DAG
ne remplace pas le choix de sobriete argumente dans le rapport pour le
coeur du programme -- c'est un ajout optionnel, demontrable, qui ne
tourne sur aucun planning recurrent reel (schedule=None : declenchement
manuel uniquement, pour la demo).

Ordre des 3 groupes = ordre reel de dependance des donnees (staging
avant entrepot avant lake), pas un choix arbitraire :
- staging (C8-C11) : extraction brute -> nettoyage -> schema MERISE -> chargement
- entrepot OMEGA BI (C13-C15) : lit la base de staging
- data lake OMEGA LAKE (C18-C21) : `curated_bi` (C21) se joint en lecture
  aux dimensions conformees de l'entrepot (voir architecture_omega_lake.md)

Exclu volontairement : `datacore.storage.lake.sse_consumer` (C19, flux
temps reel). C'est un processus continu (`while True`), pas une tache
batch qui se termine -- l'inclure bloquerait le DAG indefiniment. Le
flux SSE n'est de toute facon pas orchestrable par un scheduler a tache
(voir chapitre 5 §"Visualiser les pipelines" du rapport).

Prerequis (hors perimetre de ce DAG, deja couverts par
docker-compose.yml) : services up, bucket MinIO et role bi_reader deja
crees (`scripts/init_omega_bi_db.sh` execute une fois depuis l'hote --
ce script shell-out vers `docker compose exec`, inutilisable depuis
l'interieur d'un conteneur).
"""
from datetime import timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, TaskGroup

WORKDIR = "cd /opt/datacore &&"

with DAG(
    dag_id="datacore_pipeline",
    description="Orchestration des pipelines staging -> entrepot OMEGA BI -> data lake OMEGA LAKE",
    schedule=None,  # declenchement manuel uniquement (demo) -- pas de planning recurrent reel
    catchup=False,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(seconds=15),
    },
    tags=["datacore", "demo"],
) as dag:

    with TaskGroup(group_id="staging_c8_c11") as staging:
        extraction = BashOperator(
            task_id="run_extraction",  # C8 : 5 sources -> data/interim/
            bash_command=f"{WORKDIR} python3 -m datacore.ingestion.run_extraction",
        )
        cleaning = BashOperator(
            task_id="run_cleaning",  # C10 : dedoublonnage fichiers clients
            bash_command=f"{WORKDIR} python3 -m datacore.processing.run_cleaning",
        )
        migrate_staging = BashOperator(
            task_id="alembic_upgrade_staging",  # C11 : schema MERISE
            bash_command=f"{WORKDIR} alembic upgrade head",
        )
        load_staging = BashOperator(
            task_id="load_staging",
            bash_command=f"{WORKDIR} python3 -m datacore.storage.staging.load_staging",
        )
        extraction >> cleaning >> migrate_staging >> load_staging

    with TaskGroup(group_id="entrepot_omega_bi_c13_c15") as entrepot:
        migrate_omega_bi = BashOperator(
            task_id="alembic_upgrade_omega_bi",  # C14 : 3 schemas + 9 tables
            bash_command=f"{WORKDIR} alembic -c alembic_omega_bi.ini upgrade head",
        )
        load_dim_temps = BashOperator(
            task_id="load_dim_temps",  # dimension calendaire generee
            bash_command=f"{WORKDIR} python3 -m datacore.storage.warehouse.load_dim_temps",
        )
        load_warehouse = BashOperator(
            task_id="load_warehouse",  # C15 : ETL staging -> entrepot
            bash_command=f"{WORKDIR} python3 -m datacore.storage.warehouse.load_warehouse",
        )
        migrate_omega_bi >> load_dim_temps >> load_warehouse

    with TaskGroup(group_id="data_lake_omega_lake_c18_c21") as lake:
        ingestion_batch = BashOperator(
            task_id="ingestion_batch",  # C19 : 4 flux IoT batch -> raw/
            bash_command=f"{WORKDIR} python3 -m datacore.storage.lake.ingestion_batch",
        )
        transform = BashOperator(
            task_id="transform",  # C18 : raw/ -> staging/ -> curated/
            bash_command=f"{WORKDIR} python3 -m datacore.storage.lake.transform",
        )
        catalogue = BashOperator(
            task_id="catalogue",  # C20 : catalogue par introspection
            bash_command=f"{WORKDIR} python3 -m datacore.storage.lake.catalogue",
        )
        curated_bi = BashOperator(
            task_id="curated_bi",  # C21 : export pseudonymise, jointure aux dims conformees
            bash_command=f"{WORKDIR} python3 -m datacore.storage.lake.curated_bi",
        )
        ingestion_batch >> transform >> catalogue >> curated_bi

    staging >> entrepot >> lake
