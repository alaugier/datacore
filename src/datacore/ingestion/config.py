"""Configuration centralisée des connecteurs d'extraction (C8).

Toutes les valeurs sont surchargeables via variables d'environnement.
Contrairement à `docker-compose` (qui lit `.env` lui-même pour les
conteneurs) ou à `scripts/init_staging_db.sh` (qui fait `source .env`),
ces scripts tournent en process Python nu sur l'hôte : `load_dotenv()`
charge donc explicitement `.env` dans l'environnement du process avant
lecture, pour que `.env` reste la source de vérité (les valeurs par
défaut ci-dessous ne servent qu'en dernier recours, ex. avant `cp
.env.example .env`).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(REPO_ROOT / ".env")

TRANSFLOW_API_URL = os.environ.get("TRANSFLOW_API_URL", "http://127.0.0.1:5050")
TRANSFLOW_API_KEY = os.environ.get("API_KEY", "datacore-training-2026")

POSTGRES_USER = os.environ.get("POSTGRES_USER", "datacore")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "datacore")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "datacore_staging")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
STAGING_DB_DSN = os.environ.get(
    "STAGING_DB_DSN",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{POSTGRES_PORT}/{POSTGRES_DB}",
)

# Entrepôt OMEGA BI (C13-C17) : base distincte de la base de staging,
# mais même instance Postgres (voir docker-compose.yml) — sobriété
# RGESN, pas de second conteneur pour une simple séparation logique.
OMEGA_BI_DB = os.environ.get("OMEGA_BI_DB", "datacore_omega_bi")
OMEGA_BI_DB_DSN = os.environ.get(
    "OMEGA_BI_DB_DSN",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{POSTGRES_PORT}/{OMEGA_BI_DB}",
)

RAW_DIR = Path(os.environ.get("DATACORE_RAW_DIR", REPO_ROOT / "data" / "raw"))
CLIENTS_FILES_DIR = RAW_DIR / "clients_fichiers"
HISTORIQUE_PATH = RAW_DIR / "historique" / "omega_historique_expeditions.csv"

# Zone d'atterrissage intermédiaire (C8) : les scripts d'extraction y
# déposent leurs résultats bruts, avant que la base de travail
# consolidée (C11, modélisation MERISE) n'existe. Non versionnée (voir
# .gitignore), au même titre que data/raw/.
INTERIM_DIR = Path(os.environ.get("DATACORE_INTERIM_DIR", REPO_ROOT / "data" / "interim"))
