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
