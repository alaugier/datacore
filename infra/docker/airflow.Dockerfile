# DAG Airflow (issue #100, stretch goal explicitement optionnel -- voir
# "Pourquoi pas un orchestrateur" au chapitre 5 du rapport). N'orchestre
# que les scripts/CLI existants tels quels (appel direct), sans
# reecriture de logique metier -- perimetre strict de l'issue.
#
# apache/airflow:3.1.8 : premiere serie 3.x a supporter SQLAlchemy >=2.0
# (ce projet utilise sqlalchemy>=2.0, incompatible avec Airflow 2.x qui
# plafonne a <2.0) -- verifie avant de choisir cette version, pas
# suppose. python3.12 pour matcher pyproject.toml (requires-python >=3.12).
FROM apache/airflow:3.1.8-python3.12

WORKDIR /opt/datacore

# --chown=airflow:root : l'image de base execute les taches en tant
# qu'utilisateur "airflow" (pas root) -- sans cela, run_extraction (C8)
# echoue a l'ecriture dans data/interim/ (cree a l'execution sous
# data/, lui-meme proprietaire root par defaut avec un simple COPY).
COPY --chown=airflow:root pyproject.toml ./
COPY --chown=airflow:root src/ ./src/
COPY --chown=airflow:root scripts/ ./scripts/
COPY --chown=airflow:root alembic.ini alembic_omega_bi.ini ./

# Donnees pedagogiques fournies (data/raw/) : non versionnees dans git
# (.gitignore) mais necessaires a C8 (run_extraction) -- copiees ici
# comme le reste du code, pas montees en volume (meme convention que
# les autres images du projet, ex. omega-data-api.Dockerfile).
COPY --chown=airflow:root data/ ./data/

# airflow-requirements.txt (sous-ensemble de requirements.txt), pas
# requirements.txt en entier -- voir le commentaire de ce fichier :
# flask>=3.0 casserait apache-airflow-providers-fab (interface web)
# sans etre necessaire a aucun script orchestre par ce DAG.
COPY --chown=airflow:root infra/docker/airflow-requirements.txt ./
RUN pip install --no-cache-dir -r airflow-requirements.txt && pip install --no-cache-dir --no-deps -e .

COPY --chown=airflow:root infra/airflow/dags/ /opt/airflow/dags/

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
