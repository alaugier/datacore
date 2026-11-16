# Script de démo live, minuté — issue #98

**Compétence couverte : démonstration du pipeline en conditions réelles, à l'oral.**
**Emplacement dans la trame** : répartie sur **5 moments live**, chacun à la
slide qui en parle déjà, plutôt qu'un seul bloc en début de deck
([`slides/slides.md`](../../slides/slides.md)) — décidé après relecture
de la v1 de ce script (bloc unique à C8) : Swagger/Grafana/MinIO/pseudonymisation
n'ont rien à voir avec « automatiser l'extraction » (C8), et un bloc
unique est un point de défaillance unique si quelque chose coince. Toutes
les commandes ci-dessous ont été exécutées et vérifiées réellement avant
l'oral (pas de commande non testée) — voir
[`chapitre 5 §6.5 du rapport`](../latex/chapitres/05_m4_restitution_bi.tex)
pour les commandes manuelles équivalentes (le DAG Airflow les appelle telles
quelles, sans les réécrire).

**Préparation, ~10 minutes avant l'oral** (hors chronométrage ci-dessous) :

```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d
docker compose -f infra/docker/docker-compose.yml --env-file .env --profile airflow up -d
```

Vérifier que tout est sain avant d'entrer en salle :
```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env ps
docker compose -f infra/docker/docker-compose.yml --env-file .env --profile airflow ps
```
Onglets navigateur à ouvrir à l'avance (dans cet ordre d'apparition dans le
deck) : `localhost:8000/docs` (Swagger), `localhost:3000` (Grafana),
`localhost:9001` (MinIO), `localhost:8080` (Airflow) — tous déjà connectés.

---

## Les 5 moments live, dans l'ordre du deck

### 1. Slide « C12 — Documentation interactive (Swagger) » (~30-40s)

Onglet Swagger (`localhost:8000/docs`) : bouton **Authorize**, coller
`omega-data-analyst-2026`, puis **Try it out** sur `GET /kpis/taux-service`,
Execute.

« L'API expose un KPI métier — taux de service par client, généré
automatiquement par FastAPI, pas écrit à la main. »

### 2. Slide « C16bis — Restitution OMEGA BI » (~20-30s)

Onglet Grafana (`localhost:3000`), dashboard SLA OMEGA BI déjà ouvert.

« Même type de donnée, vue BI — taux de service, délai moyen, stock
disponible, les trois chiffres déjà cités sur la slide. »

### 3. Slide « C19 — MinIO en conditions réelles » (~20-30s)

Onglet MinIO (`localhost:9001`), bucket `omega-lake`, montrer les préfixes
`raw/`, `staging/`, `curated/`, `curated_bi/`.

« Le data lake suit la même convention de zones que le rapport décrit —
infrastructure réelle, pas une maquette. »

### 4. Slide « C21 — Gouvernance : le parcours de la pseudonymisation » (~45s), après avoir déroulé les 5 étapes

Terminal, requête DuckDB pseudonymisée :

```bash
python3 -c "
import duckdb
con = duckdb.connect()
con.sql(\"INSTALL httpfs; LOAD httpfs;\")
con.sql(\"\"\"
    SET s3_endpoint='localhost:9000';
    SET s3_access_key_id='lake_reader';
    SET s3_secret_access_key='datacore_lake_reader';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
\"\"\")
print(con.sql(\"SELECT vehicule_id, timestamp, lat, lon FROM read_parquet('s3://omega-lake/curated_bi/geoloc_flotte/part-0.parquet') LIMIT 5\"))
"
```

« Et la preuve que ça fonctionne : `vehicule_id` est un hash, pas
l'identifiant réel, dans l'export BI — avec les identifiants `lake_reader`,
en lecture seule, jamais les identifiants admin MinIO. »

Si le jury demande à voir l'identifiant réel pour comparer : la même
requête sur `curated/geoloc_flotte/part-0.parquet` (sans `_bi`) montre
`VH-001`, etc., en clair — zone interne, jamais exposée à `lake_reader`.

### 5. Slide « Airflow — orchestration (stretch goal) » (~30s), en toute fin de deck

Onglet Airflow (`localhost:8080`) déjà ouvert — cliquer **Trigger** sur
`datacore_pipeline`.

« On déclenche le pipeline complet en direct — staging, entrepôt, data
lake, 12 tâches. » Pendant l'exécution (~20-25s réels, vue Grid),
commenter les 3 groupes qui passent au vert : `staging_c8_c11` (dont
`reset_staging` en tête, pour que ce soit rejouable à l'identique),
`entrepot_omega_bi_c13_c15`, `data_lake_omega_lake_c18_c21`. « Douze
tâches réussies — c'est tout le pipeline présenté depuis le début de
l'oral, rejoué en 25 secondes. »

**C'est délibérément le seul endroit du deck où le DAG est déclenché** —
pas en avance à C8 : le déclenchement et l'explication de l'orchestration
restent au même moment, pas séparés de plusieurs dizaines de minutes.

---

## Plan de repli

Chaque étape a une capture d'écran déjà en secours, affichée sur la slide
elle-même dans [`slides/slides.md`](../../slides/slides.md) (pas besoin
d'aller la chercher ailleurs) : `swagger_omega_data_api.png`,
`gestion_operationnelle_omega_bi_dashboard_grafana.png`,
`minio_console_buckets.png`, `airflow_dag_run_success.png`. Annoncer
simplement : « Je vous montre la capture, l'environnement réel est
disponible après la soutenance si vous voulez le reprendre en main. »

Si Airflow lui-même est injoignable (cas le plus grave, en toute fin de
deck) : repli sur les commandes manuelles du
[chapitre 5 §6.5 du rapport](../latex/chapitres/05_m4_restitution_bi.tex)
— ce sont exactement les mêmes commandes que celles appelées par
[`infra/airflow/dags/datacore_pipeline.py`](../../infra/airflow/dags/datacore_pipeline.py)
(aucune divergence possible, le DAG ne fait qu'appeler ces scripts tels
quels), seulement tapées une par une au lieu d'être orchestrées. Dans ce
cas, prévenir le jury avant de commencer : « Un souci réseau empêche
l'interface Airflow, je vous montre les mêmes étapes en ligne de
commande. »

## Visualiser les bases (staging, entrepôt) si le jury le demande

Hors script minuté (pas un moment prévu par défaut, seulement si
demandé) : DBeaver sous Windows, connecté à `localhost:5432` — WSL2
redirige `localhost` entre Windows et WSL2 automatiquement, aucune
configuration réseau supplémentaire nécessaire. Deux connexions
distinctes et nommées (`DATA CORE — Staging`, base `datacore_staging` ;
`DATA CORE — Entrepôt OMEGA BI`, base `datacore_omega_bi`), mêmes
identifiants (`datacore`/`datacore`) — testé et fonctionnel.

## Si une question très technique porte sur « ce qui s'exécute réellement »

Les commandes du chapitre 5 §6.5 sont la référence lisible ; le fichier
[`infra/airflow/dags/datacore_pipeline.py`](../../infra/airflow/dags/datacore_pipeline.py)
les contient identiques, dans les `bash_command=` de chaque tâche — ce
n'est pas une réécriture, juste un appel direct. Pointer l'un ou l'autre
selon ce que le jury demande à voir (la commande elle-même, ou comment
elle est orchestrée).
