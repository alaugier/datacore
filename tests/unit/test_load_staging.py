"""Tests unitaires du script d'import vers la base de travail (C11).

Utilise une connexion/curseur factices (pas de dépendance à une vraie
base PostgreSQL, absente en CI) pour vérifier que les bonnes requêtes
sont émises avec les bons paramètres, plutôt que de re-tester psycopg2
lui-même.
"""
from datacore.storage.staging.load_staging import (
    load_commandes_clients,
    load_lignes_commande_clients,
    load_livraisons,
    load_tournees,
    load_transporteurs,
)


class FakeCursor:
    """Curseur factice : enregistre les appels reçus et simule RETURNING id."""

    def __init__(self):
        self.executemany_calls = []
        self.execute_calls = []
        self._next_id = 1
        self._last_returning_id = None

    def executemany(self, sql, records):
        self.executemany_calls.append((sql, list(records)))

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))
        if "RETURNING id" in sql:
            self._last_returning_id = self._next_id
            self._next_id += 1

    def fetchone(self):
        return (self._last_returning_id,)


class FakeConnection:
    """Connexion factice exposant un unique curseur factice réutilisé."""

    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj


def test_load_transporteurs_inserts_and_resets_sequence():
    """Les id TransFlow sont préservés et la séquence Postgres resynchronisée."""
    conn = FakeConnection()
    records = [{"id": 1, "nom": "RapidFret", "contact": "contact@rapidfret.example"}]

    n = load_transporteurs(conn, records)

    assert n == 1
    sql, passed_records = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO transporteurs" in sql
    assert passed_records == records
    assert any("setval" in sql for sql, _ in conn.cursor_obj.execute_calls)


def test_load_transporteurs_skips_setval_when_no_records():
    """Sans enregistrement, pas de resynchronisation de séquence inutile."""
    conn = FakeConnection()

    n = load_transporteurs(conn, [])

    assert n == 0
    assert conn.cursor_obj.execute_calls == []


def test_load_tournees_inserts_with_expected_columns():
    """Les tournées sont insérées avec transporteur_id, date et chauffeur."""
    conn = FakeConnection()
    records = [
        {
            "id": 1,
            "transporteur_id": 1,
            "date": "2025-12-24",
            "vehicule_id": "VH-004",
            "chauffeur": "Yanis L.",
        }
    ]

    n = load_tournees(conn, records)

    assert n == 1
    sql, passed_records = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO tournees" in sql
    assert passed_records == records


def test_load_livraisons_inserts_without_statut_column():
    """Les livraisons sont insérées sans colonne statut (retirée, cf. vue dédiée)."""
    conn = FakeConnection()
    records = [
        {
            "id": 1,
            "tournee_id": 1,
            "tracking_number": "OMG0000001",
            "adresse_livraison": "11 rue de la Republique, Toulon",
            "heure_estimee": "15:15",
            "heure_reelle": "16:45",
        }
    ]

    n = load_livraisons(conn, records)

    assert n == 1
    sql, _ = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO livraisons" in sql
    assert "statut" not in sql


def test_load_commandes_clients_deduplicates_headers_by_client_and_commande_id():
    """Une commande multi-produits ne produit qu'un seul en-tête."""
    conn = FakeConnection()
    records = [
        {
            "client": "NordDrive",
            "commande_id": "ND-000549",
            "date_commande": "2026-07-19",
            "entrepot": "OMG-LIL",
            "sku": "SKU-10005",
            "quantite": 17,
        },
        {
            "client": "NordDrive",
            "commande_id": "ND-000549",
            "date_commande": "2026-07-19",
            "entrepot": "OMG-LIL",
            "sku": "SKU-10004",
            "quantite": 40,
        },
    ]

    header_ids = load_commandes_clients(conn, records)

    assert header_ids == {("NordDrive", "ND-000549"): 1}
    assert len(conn.cursor_obj.execute_calls) == 1


def test_load_lignes_commande_clients_uses_header_ids_mapping():
    """Chaque ligne référence l'id d'en-tête correspondant à sa commande."""
    conn = FakeConnection()
    records = [
        {"client": "NordDrive", "commande_id": "ND-000549", "sku": "SKU-10005", "quantite": 17},
        {"client": "NordDrive", "commande_id": "ND-000549", "sku": "SKU-10004", "quantite": 40},
    ]
    header_ids = {("NordDrive", "ND-000549"): 42}

    n = load_lignes_commande_clients(conn, records, header_ids)

    assert n == 2
    sql, passed_rows = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO lignes_commande_clients" in sql
    assert all(row["commande_client_id"] == 42 for row in passed_rows)
    assert {row["sku"] for row in passed_rows} == {"SKU-10005", "SKU-10004"}
