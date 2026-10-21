# DATA CORE — Omega Logistics

Programme de refonte de l'infrastructure data (formation Simplon).
4 blocs de compétences : cadrage (M0-M0), collecte/stockage (M1),
entrepôt OMEGA BI (M2), data lake OMEGA LAKE (M3).

## Structure
Voir `docs/architecture/` pour l'AS IS/TO BE et le détail des modules `src/datacore/`.

## Setup local
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # installe aussi le package datacore en editable
cd api-mock && python3 app.py   # API mock TransFlow sur :5050
```

## Qualité de code (CI)
Les mêmes vérifications que `.github/workflows/ci.yml` (lint, typage,
tests), à lancer localement avant de pousser :

```bash
ruff check .
mypy
pytest tests/unit tests/integration -v
```

## Setup via Docker Compose
Alternative conteneurisée : base de staging PostgreSQL + API mock TransFlow.

```bash
cp .env.example .env
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d --build
```

- API mock disponible sur `http://localhost:5050` (voir `.env` pour le port).
- Base de staging PostgreSQL disponible sur `localhost:5432` (utilisateur/mot
  de passe/port définis dans `.env`).

Une fois `data/raw/` peuplé avec le pack technique (voir section
« Données » ci-dessous), initialisez le schéma FluxPro et importez les 7
CSV dans la base de staging :

```bash
./scripts/init_staging_db.sh
```

Pour arrêter et supprimer les conteneurs (les données Postgres sont
conservées dans un volume nommé) :

```bash
docker compose -f infra/docker/docker-compose.yml down
```

## Données
`data/raw/` contient le pack pédagogique fourni (non versionné, voir .gitignore).

## Extraction des données (C8)
Une fois l'API mock lancée (localement ou via Docker Compose) et la base
de staging peuplée (`./scripts/init_staging_db.sh`), les cinq sources du
programme (TransFlow, portail transporteur, FluxPro, fichiers clients,
historique) peuvent être extraites en une commande :

```bash
python3 -m datacore.ingestion.run_extraction
```

Les résultats sont écrits dans `data/interim/` (zone d'atterrissage
intermédiaire, non versionnée — voir
`docs/architecture/sequencement_bloc2.md`), en attendant la modélisation
de la base de travail consolidée (C11).

## Nettoyage des fichiers clients (C10)
Une fois l'extraction (C8) effectuée, agrège et nettoie les trois
fichiers clients (dédoublonnage au grain commande/produit, dates et
unités homogénéisées) en un jeu de données unique :

```bash
python3 -m datacore.processing.run_cleaning
```

Écrit `data/interim/clients_consolidated.json` et affiche un rapport de
nettoyage (lignes lues, entrées corrompues supprimées, doublons résolus).

## Requêtes SQL d'extraction (C9)
Charge l'historique volumineux dans la base de staging (table dédiée
`historique_expeditions`) :

```bash
./scripts/load_historique.sh
```

Les requêtes documentées (commandes, stocks, expéditions FluxPro et
historique) sont dans `sql/extraction/` — voir
`docs/architecture/requetes_sql_extraction.md` pour le détail de chacune
avec un échantillon de résultat. Exécution directe, par exemple :

```bash
docker compose -f infra/docker/docker-compose.yml exec -T db \
  psql -U datacore -d datacore_staging < sql/extraction/01_commandes_par_client_periode.sql
```

## Base de travail consolidée — modélisation MERISE (C11)
Crée les tables modélisées pour C11 (`transporteurs`, `tournees`,
`livraisons`, `commandes_clients`), versionnées via Alembic — voir
`docs/architecture/modelisation_merise.md` pour le MCD complet et
`docs/architecture/registre_rgpd.md` pour le registre RGPD associé :

```bash
alembic upgrade head
```

Puis, une fois C8 et C10 exécutés, importe les données consolidées :

```bash
python3 -m datacore.storage.staging.load_staging
```

## Omega Data API (C12)
API REST documentée (spécification OpenAPI générée automatiquement),
authentifiée par clé API et autorisée par rôle (Data Engineer, Data
Analyst, référent client externe) — voir
`docs/architecture/api_omega_data.md` pour le détail des endpoints et
du modèle d'accès :

```bash
uvicorn datacore.api.main:app --reload
# -> http://127.0.0.1:8000/docs
```

Ou via Docker Compose (service `omega-data-api`, inclus dans
`docker compose up`) :

```bash
curl -H "X-API-Key: omega-data-engineer-2026" http://localhost:8000/commandes-clients
```

## Entrepôt OMEGA BI (C13-C17)
Modélisation en étoile/flocon (bottom-up, 2 datamarts, dimensions
conformées) — voir `docs/architecture/modelisation_omega_bi.md`. Créé
dans une base Postgres distincte (`datacore_omega_bi`, même instance que
la base de staging), 3 schémas Postgres créés à ce stade (`dimensions`,
`exploitation`, `commercial`), versionnée via un second environnement
Alembic — voir `docs/architecture/creation_entrepot_omega_bi.md` pour la
procédure complète (les schémas `gouvernance` et `monitoring` rejoignent
la même base plus tard, respectivement en C16 et au jalon M4). Peuplé
depuis la base de staging par un pipeline ETL
(rechargement complet, quarantaine des lignes historique non
rapprochées) — voir `docs/architecture/pipelines_etl_omega_bi.md`.
`dimensions.dim_client` est historisée (SCD2, C17) : seule dimension
jamais tronquée par le pipeline — voir
`docs/architecture/historisation_dim_client_scd2.md`. Gestion
opérationnelle (sauvegardes, journalisation, tableau de bord SLA,
registre RGPD — C16) : voir
`docs/architecture/gestion_operationnelle_omega_bi.md` et
`docs/architecture/registre_rgpd_entrepot.md` :

```bash
./scripts/init_omega_bi_db.sh
alembic -c alembic_omega_bi.ini upgrade head
python3 -m datacore.storage.warehouse.load_dim_temps
python3 -m datacore.storage.warehouse.load_warehouse
./scripts/backup_omega_bi.sh --partiel
python3 -m datacore.governance.audit_rgpd
```

**Restitution BI (C16bis)** : le tableau de bord SLA est aussi disponible
dans Grafana (outil de BI dédié, voir
`docs/architecture/gestion_operationnelle_omega_bi.md` §3.5) —
`docker compose -f infra/docker/docker-compose.yml --env-file .env up -d grafana`,
puis http://localhost:3000 (identifiants `GRAFANA_ADMIN_USER`/
`GRAFANA_ADMIN_PASSWORD` de `.env`). Connecté en lecture seule via
`bi_reader`, jamais avec les identifiants admin Postgres. Le notebook
(`notebooks/tableau_de_bord_sla_omega_bi.ipynb`) reste la preuve
exploratoire complémentaire (voir `docs/comptes_rendus/M2.md` §5).

## Data lake OMEGA LAKE (C18-C21)
Stockage objet MinIO (compatible S3), zones `raw`/`staging`/`curated` —
voir `docs/architecture/architecture_omega_lake.md` pour l'architecture
et `docs/architecture/integration_infrastructure_omega_lake.md` pour
l'intégration de MinIO. Ingestion des 4 flux IoT batch et du flux temps
réel (SSE), puis transformation (DuckDB/`httpfs`) et catalogue par
introspection :

```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d minio minio-init
python3 -m datacore.storage.lake.ingestion_batch  # C19 : 4 flux IoT batch -> raw/
python3 -m datacore.storage.lake.sse_consumer     # C19 : flux temps reel -> raw/ (continu)
python3 -m datacore.storage.lake.transform        # C18 : raw/ -> staging/ -> curated/
python3 -m datacore.storage.lake.catalogue        # C20 : catalogue par introspection
python3 -m datacore.storage.lake.curated_bi       # C21 : export pseudonymisé (bi_reader)
```

Gouvernance RGPD (risque de ré-identification `vehicule_id`/
`tournees.chauffeur`, pseudonymisation HMAC, procédure de purge) — voir
`docs/architecture/registre_rgpd_lake.md` :

```bash
python3 -m datacore.governance.audit_rgpd
python3 -m datacore.storage.lake.purge
```

## Monitoring du data lake OMEGA LAKE (C20bis)
Suivi applicatif (fraîcheur/volumétrie par flux, dernière purge RGPD) et
matériel (MinIO accessible, capacité utilisée), avec une alerte e-mail
réelle en cas de rupture de service — voir
`docs/architecture/monitoring_lake.md` :

```bash
alembic -c alembic_omega_bi.ini upgrade head
python3 -m datacore.storage.lake.monitoring
docker compose -f infra/docker/docker-compose.yml --env-file .env \
    up -d grafana alerting-webhook mailhog
```

Dashboard : http://localhost:3000/d/monitoring-lake — e-mails d'alerte
capturés localement (jamais un vrai fournisseur externe) dans MailHog :
http://localhost:8025.
