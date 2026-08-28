#!/usr/bin/env bash
# Cree la base Postgres de l'entrepot OMEGA BI (meme instance que la base
# de staging, voir infra/docker/docker-compose.yml) et un role de lecture
# seule pour les equipes BI (C14 -- "acces configures").
#
# Prerequis : `docker compose -f infra/docker/docker-compose.yml up -d`.
# Le schema lui-meme (tables/schemas Postgres dimensions/exploitation/
# commercial) est cree ensuite par `alembic -c alembic_omega_bi.ini
# upgrade head`, pas par ce script.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Fichier .env introuvable : copiez .env.example en .env avant de lancer ce script." >&2
  exit 1
fi
set -a
source .env
set +a

COMPOSE=(docker compose -f infra/docker/docker-compose.yml)
PG_USER="${POSTGRES_USER:-datacore}"
OMEGA_BI_DB="${OMEGA_BI_DB:-datacore_omega_bi}"
BI_READER_PASSWORD="${BI_READER_PASSWORD:-datacore_bi_reader}"

echo "Attente de la disponibilite de Postgres..."
until "${COMPOSE[@]}" exec -T db pg_isready -U "$PG_USER" >/dev/null 2>&1; do
  sleep 1
done

echo "Creation de la base $OMEGA_BI_DB (si absente)..."
"${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d postgres -tc \
  "SELECT 1 FROM pg_database WHERE datname = '$OMEGA_BI_DB'" | grep -q 1 || \
  "${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d postgres -c "CREATE DATABASE $OMEGA_BI_DB"

echo "Creation du role de lecture seule bi_reader (si absent)..."
"${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d postgres -tc \
  "SELECT 1 FROM pg_roles WHERE rolname = 'bi_reader'" | grep -q 1 || \
  "${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d postgres -c \
    "CREATE ROLE bi_reader LOGIN PASSWORD '$BI_READER_PASSWORD'"

echo "Base $OMEGA_BI_DB prete. Lancez ensuite :"
echo "  alembic -c alembic_omega_bi.ini upgrade head"
