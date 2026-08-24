#!/usr/bin/env bash
# Cree le schema FluxPro et importe les 7 CSV dans la base de staging
# Postgres demarree via infra/docker/docker-compose.yml.
#
# Prerequis : `docker compose -f infra/docker/docker-compose.yml up -d`
# et le pack technique present dans data/raw/ (voir README, non versionne).
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Fichier .env introuvable : copiez .env.example en .env avant de lancer ce script." >&2
  exit 1
fi
set -a
source .env
set +a

RAW_DIR="data/raw"
SCHEMA_FILE="$RAW_DIR/schema.sql"

if [ ! -f "$SCHEMA_FILE" ]; then
  echo "Pack technique introuvable ($SCHEMA_FILE)." >&2
  echo "Copiez le contenu de datacore-dataset/data dans data/raw/ avant de lancer ce script." >&2
  exit 1
fi

COMPOSE=(docker compose -f infra/docker/docker-compose.yml)
PG_USER="${POSTGRES_USER:-datacore}"
PG_DB="${POSTGRES_DB:-datacore_staging}"

echo "Attente de la disponibilite de la base de staging..."
until "${COMPOSE[@]}" exec -T db pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; do
  sleep 1
done

echo "Creation du schema FluxPro..."
"${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d "$PG_DB" < "$SCHEMA_FILE"

# Ordre d'import respectant les cles etrangeres (voir data/raw/schema.sql)
ORDER=(entrepots clients produits commandes lignes_commande expeditions stocks)

for table in "${ORDER[@]}"; do
  csv_file="$RAW_DIR/${table}.csv"
  if [ ! -f "$csv_file" ]; then
    echo "Fichier manquant : $csv_file" >&2
    exit 1
  fi
  echo "Import de la table $table depuis $csv_file..."
  "${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d "$PG_DB" \
    -c "\\copy $table FROM STDIN DELIMITER ',' CSV HEADER" < "$csv_file"
done

echo "Import termine."
