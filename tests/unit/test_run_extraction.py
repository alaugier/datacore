"""Tests unitaires de l'orchestration de l'extraction (C8), volet scraping (issue #104).

Connexion Postgres (journalisation) et appels réseau (scraping) remplacés
par des fakes -- même principe que les autres tests de ce projet.
"""
import requests

from datacore.ingestion import run_extraction


class FakeCursor:
    def __init__(self):
        self.execute_calls = []
        self._next_id = 1

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))

    def fetchone(self):
        row = (self._next_id,)
        self._next_id += 1
        return row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass

    def close(self):
        pass


def test_extract_portail_journalise_le_nombre_de_colis_et_les_erreurs_http(monkeypatch):
    """Les colis en échec (404) sont comptés comme erreurs, pas une exception qui
    interromprait le scraping des colis suivants -- et le résumé journalisé reflète
    les deux comptes (succès et erreurs), pas seulement le total brut."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.governance.journal.psycopg2.connect", lambda dsn: conn)
    monkeypatch.setattr(
        "datacore.ingestion.run_extraction.portail_scraping.scrape_colis_list",
        lambda: ["ND-001", "ND-002", "ND-003"],
    )

    def fake_detail(tn):
        if tn == "ND-002":
            raise requests.HTTPError("404 Not Found")
        return {"tracking_number": tn}

    monkeypatch.setattr(
        "datacore.ingestion.run_extraction.portail_scraping.scrape_colis_detail", fake_detail
    )
    ecrits = []
    monkeypatch.setattr(
        "datacore.ingestion.run_extraction.write_records",
        lambda records, path: ecrits.append((records, path)),
    )

    run_extraction.extract_portail()

    # Les 2 colis valides sont ecrits, le 3e (404) est exclu sans interrompre les autres.
    records, _ = ecrits[0]
    assert records == [{"tracking_number": "ND-001"}, {"tracking_number": "ND-003"}]

    # Journalisation : un INSERT (debut) puis un UPDATE (succes, avec le resume).
    calls = conn.cursor_obj.execute_calls
    assert len(calls) == 2
    update_sql, update_params = calls[1]
    assert "succes" in update_sql
    assert "2 colis scrapés, 1 erreur(s) HTTP" in update_params


def test_extract_portail_sans_aucune_erreur(monkeypatch):
    """Quand tout réussit, le résumé journalisé indique 0 erreur, pas une omission."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.governance.journal.psycopg2.connect", lambda dsn: conn)
    monkeypatch.setattr(
        "datacore.ingestion.run_extraction.portail_scraping.scrape_colis_list",
        lambda: ["ND-010"],
    )
    monkeypatch.setattr(
        "datacore.ingestion.run_extraction.portail_scraping.scrape_colis_detail",
        lambda tn: {"tracking_number": tn},
    )
    monkeypatch.setattr(
        "datacore.ingestion.run_extraction.write_records", lambda records, path: None
    )

    run_extraction.extract_portail()

    update_sql, update_params = conn.cursor_obj.execute_calls[1]
    assert "1 colis scrapés, 0 erreur(s) HTTP" in update_params
