"""Catalogue automatisé du contenu réel du data lake OMEGA LAKE (C20).

Introspection, pas documentation statique : le catalogue est **généré**
en interrogeant MinIO (`boto3`, taille/date de dépôt) et DuckDB
(`DESCRIBE`, schéma réel des fichiers) plutôt que maintenu à la main —
même principe que `datacore.governance.audit_rgpd` (C16), qui interroge
`information_schema.columns` plutôt que de documenter une liste figée.
Un catalogue à jour à chaque exécution ne peut pas devenir obsolète
silencieusement, contrairement à un tableau Markdown recopié une fois.
"""
from typing import Any

from datacore.storage.lake.transform import FLUX, lecture_raw

ZONES = ("raw", "staging", "curated")

# Origine de chaque flux -- information statique (d'où vient la donnée),
# pas observable par introspection du lake lui-même.
SOURCES = {
    "capteurs_temperature": (
        "IoT batch — capteurs de température (data/raw/iot/capteurs_temperature.csv)"
    ),
    "geoloc_flotte": "IoT batch — géolocalisation de flotte (data/raw/iot/geoloc_flotte.csv)",
    "camera_comptage": "IoT batch — comptage caméra (data/raw/iot/camera_comptage.csv)",
    "rfid_scans": "IoT batch — scans RFID palette (data/raw/iot/rfid_scans.json)",
    "flux_sse_capteurs": "IoT streaming — flux temps réel (/api/stream/capteurs, SSE)",
}

FORMATS_RAW = {
    "capteurs_temperature": "csv",
    "geoloc_flotte": "csv",
    "camera_comptage": "csv",
    "rfid_scans": "json",
    "flux_sse_capteurs": "ndjson",
}


def _lecture_zone(flux: str, zone: str, bucket: str) -> str:
    """Fragment SQL DuckDB lisant le contenu réel d'un flux/zone donné."""
    if zone == "raw":
        return lecture_raw(flux, bucket)
    return f"read_parquet('s3://{bucket}/{zone}/{flux}/part-0.parquet')"


def _entree_existe(s3, flux: str, zone: str, bucket: str) -> bool:
    """Vérifie qu'au moins un objet existe pour ce flux/zone avant d'introspecter."""
    prefixe = f"{zone}/{flux}/"
    reponse = s3.list_objects_v2(Bucket=bucket, Prefix=prefixe, MaxKeys=1)
    return bool(reponse.get("KeyCount", 0) > 0)


def catalogue_entree(con, s3, flux: str, zone: str, bucket: str) -> dict[str, Any] | None:
    """Construit l'entrée de catalogue d'un flux/zone, par introspection réelle.

    Args:
        con: connexion DuckDB ouverte (voir `transform.connexion()`).
        s3: client S3 (boto3).
        flux: nom du flux (voir `transform.FLUX`).
        zone: `"raw"`, `"staging"` ou `"curated"`.
        bucket: bucket cible.

    Returns:
        Un dict `source`/`zone`/`format`/`schema`/`nb_lignes`/
        `derniere_modification` — `None` si aucun objet n'existe encore
        pour ce flux/zone (rien à cataloguer, pas une erreur).
    """
    if not _entree_existe(s3, flux, zone, bucket):
        return None

    lecture = _lecture_zone(flux, zone, bucket)
    schema_brut = con.sql(f"DESCRIBE SELECT * FROM {lecture}").fetchall()
    schema = [{"colonne": nom, "type": type_} for nom, type_, *_ in schema_brut]
    nb_lignes = con.sql(f"SELECT count(*) FROM {lecture}").fetchone()[0]

    objets = s3.list_objects_v2(Bucket=bucket, Prefix=f"{zone}/{flux}/")["Contents"]
    derniere_modification = max(o["LastModified"] for o in objets)

    return {
        "flux": flux,
        "zone": zone,
        "source": SOURCES[flux],
        "format": FORMATS_RAW[flux] if zone == "raw" else "parquet",
        "schema": schema,
        "nb_lignes": nb_lignes,
        "derniere_modification": derniere_modification.isoformat(),
    }


def construire_catalogue(con, s3, bucket: str) -> list[dict[str, Any]]:
    """Construit le catalogue complet : une entrée par flux/zone réellement présent.

    Args:
        con: connexion DuckDB ouverte.
        s3: client S3.
        bucket: bucket cible.

    Returns:
        Liste d'entrées (voir `catalogue_entree`), triée par flux puis
        par zone (`raw` → `staging` → `curated`) — omet silencieusement
        les combinaisons flux/zone sans contenu réel, plutôt que de
        cataloguer un chemin théorique vide.
    """
    catalogue = []
    for flux in FLUX:
        for zone in ZONES:
            entree = catalogue_entree(con, s3, flux, zone, bucket)
            if entree is not None:
                catalogue.append(entree)
    return catalogue


def main() -> None:
    """Point d'entrée CLI : affiche le catalogue courant du lake."""
    import json

    from datacore.config import OMEGA_LAKE_BUCKET
    from datacore.storage.lake.ingestion_batch import client
    from datacore.storage.lake.transform import connexion

    catalogue = construire_catalogue(connexion(), client(), OMEGA_LAKE_BUCKET)
    print(json.dumps(catalogue, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
