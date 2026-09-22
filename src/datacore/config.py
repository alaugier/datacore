"""Configuration centralisée du programme (connexions Postgres, API TransFlow, chemins).

Partagée par `ingestion`, `processing`, `storage` (staging et warehouse)
et `api` — placée à la racine du package plutôt que sous `ingestion/`
(où elle a été conçue à l'origine pour C8) pour refléter cet usage
transverse, plutôt que de laisser croire qu'elle est spécifique à
l'extraction.

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

REPO_ROOT = Path(__file__).resolve().parents[2]

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

# Data lake OMEGA LAKE (C18-C19) : MinIO, meme instance locale que le
# reste (sobriete RGESN) -- voir docker-compose.yml et
# architecture_omega_lake.md. Bucket unique, zones raw/staging/curated
# comme prefixes internes, pas comme buckets separes.
MINIO_ROOT_USER = os.environ.get("MINIO_ROOT_USER", "datacore")
MINIO_ROOT_PASSWORD = os.environ.get("MINIO_ROOT_PASSWORD", "datacore_lake")
OMEGA_LAKE_S3_ENDPOINT = os.environ.get(
    "OMEGA_LAKE_S3_ENDPOINT", f"localhost:{os.environ.get('MINIO_API_PORT', '9000')}"
)
OMEGA_LAKE_BUCKET = os.environ.get("OMEGA_LAKE_BUCKET", "omega-lake")

RAW_DIR = Path(os.environ.get("DATACORE_RAW_DIR", REPO_ROOT / "data" / "raw"))
CLIENTS_FILES_DIR = RAW_DIR / "clients_fichiers"
HISTORIQUE_PATH = RAW_DIR / "historique" / "omega_historique_expeditions.csv"

# Zone d'atterrissage intermédiaire (C8) : les scripts d'extraction y
# déposent leurs résultats bruts, avant que la base de travail
# consolidée (C11, modélisation MERISE) n'existe. Non versionnée (voir
# .gitignore), au même titre que data/raw/.
INTERIM_DIR = Path(os.environ.get("DATACORE_INTERIM_DIR", REPO_ROOT / "data" / "interim"))
