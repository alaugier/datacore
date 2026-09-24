"""Test d'intégration du pipeline complet du data lake (C19-C21bis).

Exerce `ingestion_batch` → `transform` → `catalogue` → `curated_bi`
contre une infrastructure réelle (MinIO + Postgres, Docker Compose)
pour détecter une **dérive silencieuse entre modules** — ex. un
changement de convention de nommage dans `transform.py` que
`catalogue.py` ne suivrait plus. Les tests unitaires (fakes, isolés par
module) ne peuvent pas détecter ce genre de dérive ; seule une
exécution réelle du pipeline complet le peut.

**Ignoré (skip), pas échoué, si l'infrastructure n'est pas démarrée** —
pour ne pas casser `pytest` par défaut (la suite unitaire tourne sans
dépendance externe). À lancer explicitement avant de merger une PR qui
touche aux modules `storage/lake/` :

    docker compose -f infra/docker/docker-compose.yml up -d db minio minio-init api-mock
    pytest tests/integration/test_lake_pipeline.py -v
"""
import socket

import pytest


def _infra_disponible(hote: str, port: int, delai: float = 1.0) -> bool:
    """Teste une connexion TCP simple, sans dépendance à un client applicatif."""
    try:
        with socket.create_connection((hote, port), timeout=delai):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not (_infra_disponible("localhost", 9000) and _infra_disponible("localhost", 5432)),
    reason=(
        "MinIO/Postgres non accessibles -- lancer "
        "`docker compose -f infra/docker/docker-compose.yml up -d db minio minio-init api-mock` "
        "avant ce test"
    ),
)


@pytest.fixture(scope="module")
def pipeline():
    """Exécute le pipeline complet une seule fois pour tous les tests du module.

    Yields:
        dict: `con` (connexion DuckDB), `s3` (client S3), `bucket`.
    """
    from datacore.config import OMEGA_LAKE_BUCKET
    from datacore.storage.lake.curated_bi import construire_curated_bi_complet
    from datacore.storage.lake.ingestion_batch import client, ingerer_flux_batch
    from datacore.storage.lake.transform import (
        FLUX,
        connexion,
        construire_curated,
        construire_staging,
    )

    s3 = client()
    con = connexion()

    ingerer_flux_batch(s3=s3)
    for flux in FLUX:
        construire_staging(con, flux, OMEGA_LAKE_BUCKET)
        construire_curated(con, flux, OMEGA_LAKE_BUCKET)
    construire_curated_bi_complet(con, OMEGA_LAKE_BUCKET)

    yield {"con": con, "s3": s3, "bucket": OMEGA_LAKE_BUCKET}


def test_volumes_coherents_entre_staging_et_curated_pour_les_5_flux(pipeline):
    """Aucune jointure curated/ ne doit faire gagner ou perdre des lignes."""
    from datacore.storage.lake.transform import FLUX

    con, bucket = pipeline["con"], pipeline["bucket"]
    for flux in FLUX:
        n_staging = con.sql(
            f"SELECT count(*) FROM read_parquet('s3://{bucket}/staging/{flux}/part-0.parquet')"
        ).fetchone()[0]
        n_curated = con.sql(
            f"SELECT count(*) FROM read_parquet('s3://{bucket}/curated/{flux}/part-0.parquet')"
        ).fetchone()[0]
        assert n_staging == n_curated, f"{flux}: staging={n_staging} != curated={n_curated}"


def test_curated_bi_a_le_meme_volume_que_curated_pour_les_5_flux(pipeline):
    """L'export pseudonymisé ne doit ni ajouter ni perdre de lignes."""
    from datacore.storage.lake.transform import FLUX

    con, bucket = pipeline["con"], pipeline["bucket"]
    for flux in FLUX:
        n_curated = con.sql(
            f"SELECT count(*) FROM read_parquet('s3://{bucket}/curated/{flux}/part-0.parquet')"
        ).fetchone()[0]
        n_curated_bi = con.sql(
            f"SELECT count(*) FROM read_parquet('s3://{bucket}/curated_bi/{flux}/part-0.parquet')"
        ).fetchone()[0]
        assert n_curated == n_curated_bi, (
            f"{flux}: curated={n_curated} != curated_bi={n_curated_bi}"
        )


def test_catalogue_couvre_les_15_entrees_attendues(pipeline):
    """5 flux x 3 zones (raw/staging/curated) = 15 -- catalogue.py et transform.py doivent
    rester d'accord sur les noms de flux et la convention de clé S3."""
    from datacore.storage.lake.catalogue import construire_catalogue

    catalogue = construire_catalogue(pipeline["con"], pipeline["s3"], pipeline["bucket"])
    assert len(catalogue) == 15


def test_curated_bi_geoloc_ne_contient_aucun_identifiant_reel_en_clair(pipeline):
    """Garde-fou RGPD : aucun VH-0NN en clair ne doit fuiter dans curated_bi/."""
    con, bucket = pipeline["con"], pipeline["bucket"]

    identifiants_reels = {
        vid
        for (vid,) in con.sql(
            f"SELECT DISTINCT vehicule_id FROM read_parquet("
            f"'s3://{bucket}/curated/geoloc_flotte/part-0.parquet')"
        ).fetchall()
    }
    identifiants_curated_bi = {
        vid
        for (vid,) in con.sql(
            f"SELECT DISTINCT vehicule_id FROM read_parquet("
            f"'s3://{bucket}/curated_bi/geoloc_flotte/part-0.parquet')"
        ).fetchall()
    }

    assert identifiants_reels.isdisjoint(identifiants_curated_bi)


def test_audit_rgpd_ne_signale_aucune_colonne_suspecte_sur_le_pipeline_reel(pipeline):
    """Garde-fou non-régression : le pipeline reconstruit ne doit introduire aucune
    colonne évoquant une donnée personnelle (même contrôle que registre_rgpd_lake.md)."""
    from datacore.governance.audit_rgpd import auditer_lake

    resultat = auditer_lake(pipeline["con"], pipeline["s3"], pipeline["bucket"])
    assert resultat == {}
