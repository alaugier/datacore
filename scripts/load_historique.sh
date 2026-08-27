#!/usr/bin/env bash
# Cree la table historique_expeditions et importe le CSV volumineux
# (25 000 lignes) dans la base de staging Postgres demarree via
# infra/docker/docker-compose.yml (C9).
#
# Prerequis : `docker compose -f infra/docker/docker-compose.yml up -d`
# et le pack technique present dans data/raw/ (voir README).
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Fichier .env introuvable : copiez .env.example en .env avant de lancer ce script." >&2
  exit 1
fi
set -a
source .env
set +a

HISTORIQUE_CSV="data/raw/historique/omega_historique_expeditions.csv"
SCHEMA_FILE="sql/historique_schema.sql"

if [ ! -f "$HISTORIQUE_CSV" ]; then
  echo "Fichier manquant : $HISTORIQUE_CSV" >&2
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

echo "Creation de la table historique_expeditions..."
"${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d "$PG_DB" < "$SCHEMA_FILE"

echo "Import de l'historique depuis $HISTORIQUE_CSV..."
"${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d "$PG_DB" \
  -c "\\copy historique_expeditions FROM STDIN DELIMITER ',' CSV HEADER" < "$HISTORIQUE_CSV"

echo "Import termine."
