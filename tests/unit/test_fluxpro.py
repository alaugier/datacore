"""Tests unitaires de l'extraction FluxPro (C8).

`fetch_table()` n'utilise que des primitives SQL standard (DB-API 2.0),
ce qui permet de la tester avec sqlite3 (stdlib) en remplacement d'une
vraie base PostgreSQL, sans dépendance externe en CI.
"""
import sqlite3

import pytest

from datacore.ingestion.fluxpro import fetch_table


@pytest.fixture()
def sqlite_conn():
    """Connexion sqlite3 en mémoire avec une table `clients` de test."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE clients (id INTEGER, code TEXT, nom TEXT)")
    conn.execute("INSERT INTO clients VALUES (1, 'NORDDRIVE', 'NordDrive')")
    conn.commit()
    yield conn
    conn.close()


def test_fetch_table_returns_rows_as_dicts(sqlite_conn):
    """Chaque ligne est convertie en dict colonne -> valeur."""
    rows = fetch_table(sqlite_conn, "clients")

    assert rows == [{"id": 1, "code": "NORDDRIVE", "nom": "NordDrive"}]


def test_fetch_table_rejects_unknown_table_name(sqlite_conn):
    """Un nom de table hors liste blanche est rejeté (protection anti-injection)."""
    with pytest.raises(ValueError):
        fetch_table(sqlite_conn, "clients; DROP TABLE clients;--")
