"""Tests unitaires de la zone d'atterrissage intermédiaire (écriture/lecture JSON)."""
import datetime
import decimal

from datacore.ingestion.landing import read_records, write_records


def test_write_then_read_records_roundtrip(tmp_path):
    """Les enregistrements écrits sont relus à l'identique."""
    records = [{"id": 1, "nom": "RapidFret"}, {"id": 2, "nom": "TransUnion"}]
    path = tmp_path / "sub" / "transporteurs.json"

    write_records(records, path)

    assert read_records(path) == records


def test_write_records_creates_parent_directories(tmp_path):
    """Le dossier parent est créé automatiquement s'il n'existe pas."""
    path = tmp_path / "does" / "not" / "exist" / "out.json"

    write_records([], path)

    assert path.exists()


def test_write_records_serializes_decimal_and_date(tmp_path):
    """Decimal et date/datetime (types renvoyés par psycopg2/FluxPro) sont sérialisables."""
    records = [
        {
            "poids_kg": decimal.Decimal("5.13"),
            "date_commande": datetime.date(2026, 8, 25),
            "date_maj": datetime.datetime(2026, 8, 25, 14, 30),
        }
    ]
    path = tmp_path / "fluxpro_produits.json"

    write_records(records, path)

    result = read_records(path)
    assert result[0]["poids_kg"] == 5.13
    assert result[0]["date_commande"] == "2026-08-25"
    assert result[0]["date_maj"] == "2026-08-25T14:30:00"
