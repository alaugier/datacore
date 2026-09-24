"""Tests unitaires des fonctions pures de transform.py (C20).

Le pipeline complet (construire_staging/construire_curated) exécute du
DuckDB réel contre MinIO/Postgres réels -- pas de fake plausible pour un
moteur SQL embarqué, à la différence d'un simple client S3 (boto3).
Vérifié en conditions réelles à la place (voir
integration_infrastructure_omega_lake.md et le notebook de
vérification), même discipline que pour le mécanisme de jointure C19.
"""
from datacore.storage.lake.transform import FLUX, lecture_raw, motif_raw


def test_motif_raw_csv_pour_les_flux_batch_standards():
    """Les 3 flux CSV utilisent l'extension .csv dans le motif glob."""
    for flux in ("capteurs_temperature", "geoloc_flotte", "camera_comptage"):
        assert motif_raw(flux, bucket="omega-lake") == f"s3://omega-lake/raw/{flux}/date=*/*.csv"


def test_motif_raw_json_pour_rfid_scans():
    """rfid_scans utilise l'extension .json (liste JSON), pas .csv."""
    assert motif_raw("rfid_scans", bucket="omega-lake") == (
        "s3://omega-lake/raw/rfid_scans/date=*/*.json"
    )


def test_motif_raw_ndjson_pour_le_flux_sse():
    """Le flux SSE utilise l'extension .ndjson (parts déposés par sse_consumer)."""
    assert motif_raw("flux_sse_capteurs", bucket="omega-lake") == (
        "s3://omega-lake/raw/flux_sse_capteurs/date=*/*.ndjson"
    )


def test_lecture_raw_choisit_la_bonne_fonction_table():
    """Chaque flux est lu avec la fonction DuckDB adaptée à son format réel."""
    assert lecture_raw("capteurs_temperature", bucket="omega-lake").startswith("read_csv_auto(")
    assert lecture_raw("rfid_scans", bucket="omega-lake").startswith("read_json_auto(")
    sse = lecture_raw("flux_sse_capteurs", bucket="omega-lake")
    assert sse.startswith("read_json_auto(")
    assert "newline_delimited" in sse


def test_tous_les_flux_ont_un_motif_et_une_lecture_valides():
    """Aucun flux de FLUX ne lève d'erreur (couverture exhaustive des 5 flux)."""
    for flux in FLUX:
        assert motif_raw(flux, bucket="omega-lake").startswith("s3://omega-lake/raw/")
        assert lecture_raw(flux, bucket="omega-lake")
