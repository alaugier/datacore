"""Tests unitaires de la journalisation des opérations de maintenance (C16).

Connexion/curseur factices (pas de dépendance à une vraie base), sur le
même principe que les autres tests de ce projet.
"""
import pytest

from datacore.governance.journal import journaliser


class FakeCursor:
    """Curseur factice : simule RETURNING id via un compteur, enregistre les appels."""

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
    """Connexion factice : un unique curseur factice réutilisé, suit commit/close."""

    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.commits = 0
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def test_journaliser_enregistre_le_debut_puis_le_succes(monkeypatch):
    """Un bloc qui réussit journalise un INSERT (en_cours) puis un UPDATE (succès, détails)."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.governance.journal.psycopg2.connect", lambda dsn: conn)

    with journaliser("load_warehouse", dsn="postgresql://fake") as contexte:
        contexte["details"] = "42 lignes chargées"

    calls = conn.cursor_obj.execute_calls
    assert len(calls) == 2
    insert_sql, insert_params = calls[0]
    assert "INSERT INTO gouvernance.journal_operations" in insert_sql
    assert insert_params[0] == "load_warehouse"

    update_sql, update_params = calls[1]
    assert "UPDATE gouvernance.journal_operations" in update_sql
    assert "statut = 'succes'" in update_sql
    assert update_params[1] == "42 lignes chargées"
    assert conn.commits == 2
    assert conn.closed is True


def test_journaliser_enregistre_lechec_et_relance_lexception(monkeypatch):
    """Un bloc qui échoue journalise l'erreur (statut echec) et relance l'exception."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.governance.journal.psycopg2.connect", lambda dsn: conn)

    with pytest.raises(ValueError, match="panne simulée"):
        with journaliser("load_warehouse", dsn="postgresql://fake"):
            raise ValueError("panne simulée")

    update_sql, update_params = conn.cursor_obj.execute_calls[1]
    assert "statut = 'echec'" in update_sql
    assert update_params[1] == "panne simulée"
    assert conn.closed is True


def test_journaliser_sans_details_ecrit_details_none(monkeypatch):
    """Sans écriture explicite de contexte['details'], NULL est journalisé plutôt qu'une erreur."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.governance.journal.psycopg2.connect", lambda dsn: conn)

    with journaliser("load_dim_temps", dsn="postgresql://fake"):
        pass

    _, update_params = conn.cursor_obj.execute_calls[1]
    assert update_params[1] is None
