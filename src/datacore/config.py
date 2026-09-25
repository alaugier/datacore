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

# Pseudonymisation de vehicule_id pour l'export curated_bi/ exposé à
# lake_reader (C21bis) -- clé HMAC secrète, jamais distribuée avec le
# lake ni accessible depuis la couche lake_reader (voir
# storage/lake/curated_bi.py et registre_rgpd_lake.md §2).
#
# Délibérément SANS valeur de repli, contrairement au reste de ce module
# -- corrigé après relecture externe : un repli codé en dur pour un
# secret cryptographique est visible dans le dépôt public, donc pas un
# secret du tout ; un démarrage silencieux avec cette valeur romprait la
# pseudonymisation sans avertissement. `os.environ.get()` (pas
# `os.environ[...]`) : la variable manquante renvoie None ici plutôt que
# de faire échouer l'import de ce module pour tout le projet (`config.py`
# est partagé par des scripts qui n'utilisent jamais cette clé) --
# `storage/lake/curated_bi.py::verifier_cle_configuree()` refuse
# explicitement de continuer si elle vaut None ou la valeur d'exemple de
# .env.example, au point d'usage plutôt qu'à l'import.
LAKE_PSEUDONYM_KEY = os.environ.get("LAKE_PSEUDONYM_KEY")

# Restitution BI (C16bis) : Grafana, auto-hébergé, connecté en lecture
# seule à l'entrepôt via bi_reader (voir
# gestion_operationnelle_omega_bi.md §3.5). Identifiants admin utilisés
# uniquement par les tests d'intégration pour interroger l'API Grafana
# (santé de la source de données, contenu du dashboard) -- jamais par le
# code applicatif.
GRAFANA_ADMIN_USER = os.environ.get("GRAFANA_ADMIN_USER", "admin")
GRAFANA_ADMIN_PASSWORD = os.environ.get("GRAFANA_ADMIN_PASSWORD", "datacore_grafana")
GRAFANA_PORT = os.environ.get("GRAFANA_PORT", "3000")

# Alerte de monitoring du lake (C20bis) : rupture de service détectée
# par une règle d'alerte Grafana, relayée par un petit service Flask
# (`datacore.alerting.webhook`) qui envoie un vrai e-mail (smtplib) à
# un capteur SMTP local (MailHog) -- jamais un vrai fournisseur externe,
# voir gestion_operationnelle_omega_bi.md pour la justification.
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
ALERTING_WEBHOOK_PORT = os.environ.get("ALERTING_WEBHOOK_PORT", "5060")
MAILHOG_API_PORT = os.environ.get("MAILHOG_API_PORT", "8025")

RAW_DIR = Path(os.environ.get("DATACORE_RAW_DIR", REPO_ROOT / "data" / "raw"))
CLIENTS_FILES_DIR = RAW_DIR / "clients_fichiers"
HISTORIQUE_PATH = RAW_DIR / "historique" / "omega_historique_expeditions.csv"

# Zone d'atterrissage intermédiaire (C8) : les scripts d'extraction y
# déposent leurs résultats bruts, avant que la base de travail
# consolidée (C11, modélisation MERISE) n'existe. Non versionnée (voir
# .gitignore), au même titre que data/raw/.
INTERIM_DIR = Path(os.environ.get("DATACORE_INTERIM_DIR", REPO_ROOT / "data" / "interim"))
