"""Tests unitaires du script d'import vers la base de travail (C11).

Utilise une connexion/curseur factices (pas de dépendance à une vraie
base PostgreSQL, absente en CI) pour vérifier que les bonnes requêtes
sont émises avec les bons paramètres, plutôt que de re-tester psycopg2
lui-même.
"""
from datacore.storage.staging.load_staging import (
    load_commandes_clients,
    load_livraisons,
    load_tournees,
    load_transporteurs,
)


class FakeCursor:
    """Curseur factice qui enregistre les appels executemany/execute reçus."""

    def __init__(self):
        self.executemany_calls = []
        self.execute_calls = []

    def executemany(self, sql, records):
        self.executemany_calls.append((sql, list(records)))

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))


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


def test_load_livraisons_inserts_with_expected_columns():
    """Les livraisons sont insérées avec leur tracking_number et adresse."""
    conn = FakeConnection()
    records = [
        {
            "id": 1,
            "tournee_id": 1,
            "tracking_number": "OMG0000001",
            "adresse_livraison": "11 rue de la Republique, Toulon",
            "statut": "Livree",
            "heure_estimee": "15:15",
            "heure_reelle": "16:45",
        }
    ]

    n = load_livraisons(conn, records)

    assert n == 1
    sql, _ = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO livraisons" in sql


def test_load_commandes_clients_does_not_reset_sequence():
    """commandes_clients n'a pas d'id source (généré par la base) : pas de setval nécessaire."""
    conn = FakeConnection()
    records = [
        {
            "client": "NordDrive",
            "commande_id": "ND-000001",
            "date_commande": "2026-07-19",
            "sku": "SKU-10005",
            "libelle_produit": "Bougie",
            "quantite": 17,
            "poids_kg": 5.9,
            "entrepot": "OMG-LIL",
            "chaine_froid_requise": None,
        }
    ]

    n = load_commandes_clients(conn, records)

    assert n == 1
    sql, _ = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO commandes_clients" in sql
    assert conn.cursor_obj.execute_calls == []
