"""Tests unitaires de la couche d'accès aux données de l'Omega Data API (C12).

Utilise une connexion/curseur factices (pas de dépendance à une vraie
base PostgreSQL) pour vérifier que les bonnes requêtes sont émises avec
les bons filtres, sur le même principe que
`tests/unit/test_load_staging.py`.
"""
from datacore.api.repository import (
    get_commande_client,
    list_commandes_clients,
    list_lignes_commande_client,
    list_livraisons,
    taux_service_par_client,
)


class FakeCursor:
    """Curseur factice : rejoue des lignes préparées et enregistre les appels reçus."""

    def __init__(self, description, rows):
        self.description = description
        self._rows = rows
        self.execute_calls = []

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConnection:
    """Connexion factice exposant un unique curseur factice réutilisé."""

    def __init__(self, description, rows):
        self.cursor_obj = FakeCursor(description, rows)

    def cursor(self):
        return self.cursor_obj


def test_list_commandes_clients_filters_by_client():
    """Le filtre client est bien transmis en paramètre de la requête."""
    description = [("id",), ("client",), ("commande_id",), ("date_commande",), ("entrepot",)]
    rows = [(1, "NordDrive", "ND-000001", "2026-07-19", "OMG-LIL")]
    conn = FakeConnection(description, rows)

    result = list_commandes_clients(conn, client="NordDrive", limit=10, offset=0)

    assert result == [
        {
            "id": 1,
            "client": "NordDrive",
            "commande_id": "ND-000001",
            "date_commande": "2026-07-19",
            "entrepot": "OMG-LIL",
        }
    ]
    sql, params = conn.cursor_obj.execute_calls[0]
    assert "WHERE client = %s" in sql
    assert params == ("NordDrive", 10, 0)


def test_list_commandes_clients_without_filter():
    """Sans filtre client, aucune clause WHERE n'est ajoutée."""
    description = [("id",), ("client",), ("commande_id",), ("date_commande",), ("entrepot",)]
    conn = FakeConnection(description, [])

    list_commandes_clients(conn, client=None, limit=50, offset=0)

    sql, params = conn.cursor_obj.execute_calls[0]
    assert "WHERE" not in sql
    assert params == (50, 0)


def test_get_commande_client_returns_none_when_not_found():
    """Une commande inexistante renvoie None plutôt qu'une erreur."""
    description = [("id",), ("client",), ("commande_id",), ("date_commande",), ("entrepot",)]
    conn = FakeConnection(description, [])

    assert get_commande_client(conn, 999) is None


def test_get_commande_client_returns_dict_when_found():
    """Une commande existante est renvoyée sous forme de dict."""
    description = [("id",), ("client",), ("commande_id",), ("date_commande",), ("entrepot",)]
    rows = [(1, "NordDrive", "ND-000001", "2026-07-19", "OMG-LIL")]
    conn = FakeConnection(description, rows)

    result = get_commande_client(conn, 1)

    assert result == {
        "id": 1,
        "client": "NordDrive",
        "commande_id": "ND-000001",
        "date_commande": "2026-07-19",
        "entrepot": "OMG-LIL",
    }


def test_list_lignes_commande_client_joins_produits():
    """La jointure vers produits est bien présente (libellé/poids/temp. dirigée dérivés)."""
    description = [
        ("id",), ("sku",), ("libelle_produit",), ("quantite",),
        ("poids_kg",), ("temperature_dirigee",),
    ]
    conn = FakeConnection(description, [])

    list_lignes_commande_client(conn, 42)

    sql, params = conn.cursor_obj.execute_calls[0]
    assert "JOIN produits p ON p.sku = lcc.sku" in sql
    assert params == (42,)


def test_list_livraisons_queries_the_statut_view():
    """list_livraisons interroge la vue livraisons_avec_statut, pas la table brute."""
    description = [
        ("id",), ("tournee_id",), ("tracking_number",),
        ("heure_estimee",), ("heure_reelle",), ("statut",),
    ]
    conn = FakeConnection(description, [])

    list_livraisons(conn, statut="Livree", limit=10, offset=0)

    sql, params = conn.cursor_obj.execute_calls[0]
    assert "FROM livraisons_avec_statut" in sql
    assert "WHERE statut = %s" in sql
    assert params == ("Livree", 10, 0)


def test_taux_service_par_client_filters_when_client_given():
    """Le calcul du taux de service se restreint au client demandé si fourni."""
    description = [("client",), ("nb_expeditions",), ("taux_service_pct",)]
    conn = FakeConnection(description, [])

    taux_service_par_client(conn, client="NordDrive")

    sql, params = conn.cursor_obj.execute_calls[0]
    assert "AND c.nom = %s" in sql
    assert params == ("NordDrive",)


def test_taux_service_par_client_without_filter():
    """Sans client demandé, le calcul porte sur tous les clients."""
    description = [("client",), ("nb_expeditions",), ("taux_service_pct",)]
    conn = FakeConnection(description, [])

    taux_service_par_client(conn, client=None)

    sql, params = conn.cursor_obj.execute_calls[0]
    assert "AND c.nom" not in sql
    assert params is None
