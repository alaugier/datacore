"""Transformations `raw/` → `staging/` → `curated/` du data lake OMEGA LAKE (C20).

`staging/` et `curated/` sont **régénérables**, contrairement à `raw/`
(immuable) — voir `architecture_omega_lake.md` §3 : chaque exécution
reconstruit entièrement `part-0.parquet` depuis `raw/`, pas
d'accumulation incrémentale. Même logique de rechargement complet que
`load_warehouse.py` (C15) : plus simple à garantir correct tant que ces
zones ne portent pas d'historique propre.

**Jointures `curated/`** : seules les clés naturelles réellement conçues
et vérifiées en C18 §5 sont implémentées ici — `entrepot` →
`dimensions.dim_site.code` et `produit_sku` → `dimensions.dim_produit.sku`
(entrepôt OMEGA BI, base distincte de la base de staging). La troisième
clé identifiée en C18 (`vehicule_id` → `tournees.vehicule_id`) n'est
**volontairement pas jointe automatiquement** : décision RGPD actée en
C18 §6 (la jointure permettrait de remonter jusqu'à
`tournees.chauffeur`, donnée personnelle). `geoloc_flotte` et
`flux_sse_capteurs` restent donc typés en `staging/`/`curated/` sans
enrichissement relationnel.
"""
import duckdb

from datacore.config import (
    MINIO_ROOT_PASSWORD,
    MINIO_ROOT_USER,
    OMEGA_BI_DB,
    OMEGA_LAKE_BUCKET,
    OMEGA_LAKE_S3_ENDPOINT,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

FLUX = (
    "capteurs_temperature",
    "geoloc_flotte",
    "camera_comptage",
    "rfid_scans",
    "flux_sse_capteurs",
)

# Jointures curated/ : uniquement les 3 flux pour lesquels C18 §5 a
# identifié et vérifié une clé naturelle réelle vers l'entrepôt OMEGA BI.
_JOINTURES_CURATED = {
    "capteurs_temperature": """
        SELECT s.*, d.nom AS entrepot_nom, d.ville AS entrepot_ville
        FROM read_parquet('s3://{bucket}/staging/{flux}/part-0.parquet') s
        JOIN entrepot.dimensions.dim_site d ON d.code = s.entrepot
    """,
    "camera_comptage": """
        SELECT s.*, d.nom AS entrepot_nom, d.ville AS entrepot_ville
        FROM read_parquet('s3://{bucket}/staging/{flux}/part-0.parquet') s
        JOIN entrepot.dimensions.dim_site d ON d.code = s.entrepot
    """,
    "rfid_scans": """
        SELECT s.*, ds.nom AS entrepot_nom,
               dp.libelle AS produit_libelle, dp.temperature_dirigee
        FROM read_parquet('s3://{bucket}/staging/{flux}/part-0.parquet') s
        JOIN entrepot.dimensions.dim_site ds ON ds.code = s.entrepot
        JOIN entrepot.dimensions.dim_produit dp ON dp.sku = s.produit_sku
    """,
}


def motif_raw(flux: str, bucket: str = OMEGA_LAKE_BUCKET) -> str:
    """Construit le motif glob S3 couvrant toutes les partitions `date=` d'un flux.

    Args:
        flux: nom du flux (voir `FLUX`).
        bucket: bucket cible.

    Returns:
        Le motif `s3://<bucket>/raw/<flux>/date=*/*.<extension>`, avec
        l'extension adaptée au format réel du flux (`.ndjson` pour le
        flux SSE, `.json` pour `rfid_scans`, `.csv` pour les 3 autres).
    """
    if flux == "flux_sse_capteurs":
        extension = "ndjson"
    elif flux == "rfid_scans":
        extension = "json"
    else:
        extension = "csv"
    return f"s3://{bucket}/raw/{flux}/date=*/*.{extension}"


def lecture_raw(flux: str, bucket: str = OMEGA_LAKE_BUCKET) -> str:
    """Fragment SQL DuckDB lisant toutes les partitions `raw/` d'un flux.

    Args:
        flux: nom du flux (voir `FLUX`).
        bucket: bucket cible.

    Returns:
        Un appel de fonction table DuckDB (`read_csv_auto`/`read_json_auto`),
        utilisable directement dans une clause `FROM`.
    """
    motif = motif_raw(flux, bucket)
    if flux == "flux_sse_capteurs":
        return f"read_json_auto('{motif}', format='newline_delimited')"
    if flux == "rfid_scans":
        return f"read_json_auto('{motif}')"
    return f"read_csv_auto('{motif}')"


def connexion() -> duckdb.DuckDBPyConnection:
    """Ouvre une connexion DuckDB prête à lire MinIO et les deux bases Postgres.

    Returns:
        Connexion avec `httpfs`/`postgres` chargées, S3 configuré pour
        MinIO (pas AWS S3, voir `integration_infrastructure_omega_lake.md`
        §1.3bis), et les deux bases attachées en lecture seule : `staging`
        (base de staging, C11) et `entrepot` (OMEGA BI, C13-C17).
    """
    con = duckdb.connect()
    con.sql("INSTALL httpfs; LOAD httpfs; INSTALL postgres; LOAD postgres;")
    con.sql(f"""
        SET s3_endpoint='{OMEGA_LAKE_S3_ENDPOINT}';
        SET s3_access_key_id='{MINIO_ROOT_USER}';
        SET s3_secret_access_key='{MINIO_ROOT_PASSWORD}';
        SET s3_use_ssl=false;
        SET s3_url_style='path';
    """)
    con.sql(f"""
        ATTACH 'host=localhost port={POSTGRES_PORT} dbname={POSTGRES_DB}
                user={POSTGRES_USER} password={POSTGRES_PASSWORD}'
        AS staging (TYPE postgres, READ_ONLY)
    """)
    con.sql(f"""
        ATTACH 'host=localhost port={POSTGRES_PORT} dbname={OMEGA_BI_DB}
                user={POSTGRES_USER} password={POSTGRES_PASSWORD}'
        AS entrepot (TYPE postgres, READ_ONLY)
    """)
    return con


def construire_staging(
    con: duckdb.DuckDBPyConnection, flux: str, bucket: str = OMEGA_LAKE_BUCKET
) -> str:
    """Reconstruit `staging/<flux>/part-0.parquet` depuis toutes les partitions `raw/`.

    Déduplication basique (ligne strictement identique) — suffisant pour
    éliminer les doublons créés par une réingestion du même fichier
    source sous une nouvelle partition `date=`, pas une déduplication
    métier (clé naturelle), qui resterait à concevoir si un besoin réel
    l'exigeait.

    Args:
        con: connexion DuckDB ouverte (voir `connexion()`).
        flux: nom du flux à traiter.
        bucket: bucket cible.

    Returns:
        La clé S3 du fichier Parquet écrit.
    """
    cle = f"staging/{flux}/part-0.parquet"
    con.sql(f"""
        COPY (SELECT DISTINCT * FROM {lecture_raw(flux, bucket)})
        TO 's3://{bucket}/{cle}' (FORMAT PARQUET)
    """)
    return cle


def construire_curated(
    con: duckdb.DuckDBPyConnection, flux: str, bucket: str = OMEGA_LAKE_BUCKET
) -> str:
    """Reconstruit `curated/<flux>/part-0.parquet` depuis `staging/<flux>/`.

    Args:
        con: connexion DuckDB ouverte (voir `connexion()`).
        flux: nom du flux à traiter.
        bucket: bucket cible.

    Returns:
        La clé S3 du fichier Parquet écrit.
    """
    cle = f"curated/{flux}/part-0.parquet"
    if flux in _JOINTURES_CURATED:
        requete = _JOINTURES_CURATED[flux].format(bucket=bucket, flux=flux)
    else:
        requete = f"SELECT * FROM read_parquet('s3://{bucket}/staging/{flux}/part-0.parquet')"
    con.sql(f"COPY ({requete}) TO 's3://{bucket}/{cle}' (FORMAT PARQUET)")
    return cle


def construire_lake(con: duckdb.DuckDBPyConnection | None = None) -> dict[str, list[str]]:
    """Reconstruit `staging/` et `curated/` pour les 5 flux depuis `raw/`.

    Args:
        con: connexion DuckDB à réutiliser (paramétrable pour les tests) ;
            par défaut, une nouvelle connexion réelle est ouverte.

    Returns:
        Un dict `{flux: [clé_staging, clé_curated]}`.
    """
    con = con or connexion()
    resultat = {}
    for flux in FLUX:
        cle_staging = construire_staging(con, flux, OMEGA_LAKE_BUCKET)
        cle_curated = construire_curated(con, flux, OMEGA_LAKE_BUCKET)
        resultat[flux] = [cle_staging, cle_curated]
    return resultat


def main() -> None:
    """Point d'entrée CLI : reconstruit `staging/`/`curated/` pour les 5 flux."""
    for flux, cles in construire_lake().items():
        print(f"{flux}: {cles}")


if __name__ == "__main__":
    main()
