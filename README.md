# DATA CORE — Omega Logistics

Programme de refonte de l'infrastructure data (formation Simplon).
4 blocs de compétences : cadrage (M0-M0), collecte/stockage (M1),
entrepôt OMEGA BI (M2), data lake OMEGA LAKE (M3).

## Structure
Voir `docs/architecture/` pour l'AS IS/TO BE et le détail des modules `src/datacore/`.

## Setup local
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
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
