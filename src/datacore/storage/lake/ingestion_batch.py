"""Ingestion batch des fichiers IoT bruts vers la zone raw/ du data lake OMEGA LAKE (C19).

Copie fidèle (`architecture_omega_lake.md` §3, « raw/ : copie telle
quelle, aucune transformation ») : chaque fichier source est déposé tel
quel dans MinIO, octet pour octet. DuckDB n'intervient pas ici -- lire
puis réécrire un CSV/JSON via DuckDB reformatterait potentiellement le
contenu (quotage, ordre des clés) sans changer l'information, ce qui
romprait la fidélité exigée pour cette zone. `boto3` (client S3
générique) est utilisé à la place, précisément parce qu'il transfère
des octets sans les interpréter.
"""
import datetime
from pathlib import Path

import boto3
from botocore.client import Config

from datacore.config import (
    MINIO_ROOT_PASSWORD,
    MINIO_ROOT_USER,
    OMEGA_LAKE_BUCKET,
    OMEGA_LAKE_S3_ENDPOINT,
    RAW_DIR,
)

# Les 4 flux IoT batch -- le 5e flux (SSE, temps réel) est traité par un
# consommateur dédié, pas par cette ingestion par lots.
FLUX_BATCH = (
    "capteurs_temperature.csv",
    "geoloc_flotte.csv",
    "camera_comptage.csv",
    "rfid_scans.json",
)


def client():
    """Ouvre un client S3 (boto3) pointant vers MinIO.

    Returns:
        Un client boto3 configuré en adressage "path" -- requis par
        MinIO, qui n'accepte pas le style "virtual-hosted" par défaut
        d'AWS S3 (même remarque que pour DuckDB/httpfs, voir
        `integration_infrastructure_omega_lake.md` §1.3bis).
    """
    return boto3.client(
        "s3",
        endpoint_url=f"http://{OMEGA_LAKE_S3_ENDPOINT}",
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
        config=Config(s3={"addressing_style": "path"}),
    )


def ingerer_flux_batch(
    date_ingestion: datetime.date | None = None,
    repertoire: Path = RAW_DIR / "iot",
    s3=None,
) -> list[str]:
    """Copie les 4 fichiers IoT batch tels quels vers `omega-lake/raw/`.

    Args:
        date_ingestion: date de partition du dépôt. C'est la date à
            laquelle ce batch est déposé dans le lake, pas la date des
            événements contenus dans le fichier (qui peut couvrir
            plusieurs jours, ex. `capteurs_temperature.csv` couvre le
            01 au 03/08/2026 en une seule exécution) -- par défaut, la
            date du jour d'exécution.
        repertoire: dossier source des 4 fichiers IoT batch.
        s3: client S3 à utiliser (paramétrable pour les tests, évite
            une dépendance à une vraie instance MinIO).

    Returns:
        La liste des clés S3 déposées, une par flux.
    """
    date_ingestion = date_ingestion or datetime.date.today()
    s3 = s3 or client()
    cles = []
    for nom_fichier in FLUX_BATCH:
        chemin_local = repertoire / nom_fichier
        flux = chemin_local.stem
        cle = f"raw/{flux}/date={date_ingestion.isoformat()}/{nom_fichier}"
        s3.upload_file(str(chemin_local), OMEGA_LAKE_BUCKET, cle)
        cles.append(cle)
    return cles


def main() -> None:
    """Point d'entrée CLI : ingère les 4 flux batch avec la date du jour."""
    cles = ingerer_flux_batch()
    print(f"{len(cles)} fichiers déposés dans {OMEGA_LAKE_BUCKET}/raw/ :")
    for cle in cles:
        print(f"  - {cle}")


if __name__ == "__main__":
    main()
