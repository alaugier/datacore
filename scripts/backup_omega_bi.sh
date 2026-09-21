#!/usr/bin/env bash
# Sauvegarde de l'entrepot OMEGA BI (C16) : complete (toute la base) ou
# partielle (dimensions.dim_client uniquement).
#
# Pourquoi ce decoupage : les 7 autres tables (dimensions/faits hors
# dim_client) sont entierement reconstructibles en rejouant le pipeline
# ETL (C15) depuis le staging -- une sauvegarde n'apporte rien qu'un
# rechargement ne referait pas. dim_client est la seule exception : elle
# est historisee (SCD2, C17), donc la seule donnee reellement
# irremplacable de l'entrepot. La sauvegarde partielle, legere et rapide,
# protege specifiquement cette donnee ; la sauvegarde complete reste
# utile en secours si le staging lui-meme devenait indisponible ou si la
# logique de l'ETL changeait entre-temps.
#
# Usage :
#   ./scripts/backup_omega_bi.sh --complet
#   ./scripts/backup_omega_bi.sh --partiel
#
# Planification (exemple crontab -- sauvegarde partielle quotidienne a
# 2h, complete hebdomadaire le dimanche a 3h) :
#   0 2 * * *   cd /chemin/vers/datacore && ./scripts/backup_omega_bi.sh --partiel
#   0 3 * * 0   cd /chemin/vers/datacore && ./scripts/backup_omega_bi.sh --complet
set -euo pipefail

cd "$(dirname "$0")/.."

MODE="${1:-}"
if [ "$MODE" != "--complet" ] && [ "$MODE" != "--partiel" ]; then
  echo "Usage : $0 --complet|--partiel" >&2
  exit 1
fi

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

mkdir -p backups
HORODATAGE="$(date +%Y%m%d_%H%M%S)"
DEBUT_SQL="$(date '+%Y-%m-%d %H:%M:%S')"

if [ "$MODE" = "--complet" ]; then
  OPERATION="backup_complet"
  FICHIER="backups/omega_bi_complet_${HORODATAGE}.sql"
else
  OPERATION="backup_partiel"
  FICHIER="backups/omega_bi_partiel_dim_client_${HORODATAGE}.sql"
fi

journaliser_echec() {
  local fin
  fin="$(date '+%Y-%m-%d %H:%M:%S')"
  "${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d "$OMEGA_BI_DB" -c \
    "INSERT INTO gouvernance.journal_operations (operation, demarre_le, termine_le, statut, erreur)
     VALUES ('$OPERATION', '$DEBUT_SQL', '$fin', 'echec', 'Echec de la sauvegarde -- voir la sortie du script')" \
    >/dev/null 2>&1 || true
}
trap journaliser_echec ERR

if [ "$MODE" = "--complet" ]; then
  echo "Sauvegarde complete de $OMEGA_BI_DB vers $FICHIER..."
  "${COMPOSE[@]}" exec -T db pg_dump -U "$PG_USER" -d "$OMEGA_BI_DB" > "$FICHIER"
else
  echo "Sauvegarde partielle (dimensions.dim_client) vers $FICHIER..."
  "${COMPOSE[@]}" exec -T db pg_dump -U "$PG_USER" -d "$OMEGA_BI_DB" \
    --table=dimensions.dim_client > "$FICHIER"
fi

TAILLE="$(du -h "$FICHIER" | cut -f1)"
FIN_SQL="$(date '+%Y-%m-%d %H:%M:%S')"

echo "Sauvegarde terminee : $FICHIER ($TAILLE)."

"${COMPOSE[@]}" exec -T db psql -U "$PG_USER" -d "$OMEGA_BI_DB" -c \
  "INSERT INTO gouvernance.journal_operations (operation, demarre_le, termine_le, statut, details)
   VALUES ('$OPERATION', '$DEBUT_SQL', '$FIN_SQL', 'succes', '$FICHIER ($TAILLE)')"
