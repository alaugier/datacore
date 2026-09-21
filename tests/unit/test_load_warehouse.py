"""Tests unitaires du pipeline ETL staging -> entrepôt OMEGA BI (C15).

Connexions/curseurs factices (pas de dépendance à une vraie base), sur
le même principe que `tests/unit/test_load_staging.py` et
`tests/unit/test_api_repository.py`. La correction du SQL et des
jointures est vérifiée par un test de bout en bout contre une vraie base
(Docker Compose), documenté dans
`docs/architecture/pipelines_etl_omega_bi.md`.
"""
import datetime

import pytest

from datacore.storage.warehouse.load_warehouse import (
    _date_key,
    client_categorie_keys,
    load_dim_categorie,
    load_dim_client,
    load_fait_commande,
    load_fait_expedition_fluxpro,
    load_fait_expedition_historique,
    load_fait_stock,
    truncate_warehouse,
)


class FakeStagingCursor:
    """Curseur factice côté staging : renvoie une liste de dicts fixée, quelle
    que soit la requête."""

    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeStagingConnection:
    """Connexion factice côté staging, en lecture seule pour ce pipeline."""

    def __init__(self, rows):
        self._rows = rows

    def cursor(self, cursor_factory=None):
        return FakeStagingCursor(self._rows)


class FakeWarehouseCursor:
    """Curseur factice côté entrepôt : simule RETURNING via un compteur, enregistre les appels."""

    def __init__(self):
        self.execute_calls = []
        self.executemany_calls = []
        self._next_key = 1

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))

    def executemany(self, sql, records):
        self.executemany_calls.append((sql, list(records)))

    def fetchone(self):
        key = self._next_key
        self._next_key += 1
        return (key,)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeWarehouseConnection:
    """Connexion factice côté entrepôt, un unique curseur factice réutilisé."""

    def __init__(self):
        self.cursor_obj = FakeWarehouseCursor()

    def cursor(self):
        return self.cursor_obj


def test_date_key_convertit_en_yyyymmdd():
    """_date_key convertit une date en entier YYYYMMDD."""
    assert _date_key(datetime.date(2026, 8, 28)) == 20260828


def test_truncate_warehouse_inclut_toutes_les_tables_hors_dim_temps_et_dim_client():
    """truncate_warehouse vide les 7 tables rechargées entièrement, jamais
    dim_temps ni dim_client."""
    warehouse_conn = FakeWarehouseConnection()

    truncate_warehouse(warehouse_conn)

    sql, _ = warehouse_conn.cursor_obj.execute_calls[0]
    for table in [
        "dimensions.dim_site", "dimensions.dim_categorie",
        "dimensions.dim_produit", "dimensions.dim_transporteur",
        "exploitation.fait_expedition", "exploitation.fait_stock", "commercial.fait_commande",
    ]:
        assert table in sql
    assert "dim_temps" not in sql
    assert "dim_client" not in sql
    assert "CASCADE" in sql


class FakeScd2Cursor:
    """Curseur factice pour load_dim_client (SCD2) : SELECT (version courante) puis INSERT/UPDATE.

    Args:
        current_row: `(client_key, nom, secteur)` simulant la version
            courante déjà en base, ou `None` si le client est inédit.
    """

    def __init__(self, current_row):
        self.current_row = current_row
        self.execute_calls = []
        self._last_sql = None
        self._next_key = 100

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))
        self._last_sql = sql

    def fetchone(self):
        if "SELECT client_key, nom, secteur" in self._last_sql:
            return self.current_row
        if "RETURNING client_key" in self._last_sql:
            key = self._next_key
            self._next_key += 1
            return (key,)
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeScd2Connection:
    """Connexion factice câblée sur un FakeScd2Cursor pré-configuré."""

    def __init__(self, current_row):
        self.cursor_obj = FakeScd2Cursor(current_row)

    def cursor(self):
        return self.cursor_obj


def test_load_dim_client_premiere_version_insere_sans_cloturer_rien():
    """Un client jamais vu (aucune version courante) est simplement inséré."""
    staging_conn = FakeStagingConnection([
        {"id": 1, "code": "NORDDRIVE", "nom": "NordDrive", "secteur": "Pieces automobiles"},
    ])
    warehouse_conn = FakeScd2Connection(current_row=None)

    mapping = load_dim_client(staging_conn, warehouse_conn, today=datetime.date(2026, 9, 21))

    assert mapping == {1: 100}
    calls = warehouse_conn.cursor_obj.execute_calls
    assert len(calls) == 2  # SELECT puis INSERT, pas d'UPDATE
    assert "UPDATE" not in calls[1][0]
    assert "INSERT INTO dimensions.dim_client" in calls[1][0]


def test_load_dim_client_reutilise_la_version_inchangee():
    """Sans changement de nom/secteur, la ligne existante est réutilisée, rien n'est écrit."""
    staging_conn = FakeStagingConnection([
        {"id": 1, "code": "NORDDRIVE", "nom": "NordDrive", "secteur": "Pieces automobiles"},
    ])
    warehouse_conn = FakeScd2Connection(current_row=(555, "NordDrive", "Pieces automobiles"))

    mapping = load_dim_client(staging_conn, warehouse_conn, today=datetime.date(2026, 9, 21))

    assert mapping == {1: 555}
    calls = warehouse_conn.cursor_obj.execute_calls
    assert len(calls) == 1  # uniquement le SELECT


def test_load_dim_client_historise_un_changement_de_secteur():
    """Un secteur modifié clôture l'ancienne version et en ouvre une nouvelle."""
    staging_conn = FakeStagingConnection([
        {
            "id": 1, "code": "NORDDRIVE", "nom": "NordDrive",
            "secteur": "Pieces automobiles et electromobilite",
        },
    ])
    warehouse_conn = FakeScd2Connection(current_row=(4, "NordDrive", "Pieces automobiles"))

    mapping = load_dim_client(staging_conn, warehouse_conn, today=datetime.date(2026, 9, 21))

    assert mapping == {1: 100}  # nouvelle client_key, pas l'ancienne (4)
    calls = warehouse_conn.cursor_obj.execute_calls
    assert len(calls) == 3  # SELECT, UPDATE (clôture), INSERT (nouvelle version)
    update_sql, update_params = calls[1]
    assert "UPDATE dimensions.dim_client" in update_sql
    assert "is_current = false" in update_sql
    assert update_params["client_key"] == 4
    assert update_params["today"] == datetime.date(2026, 9, 21)
    insert_sql, insert_params = calls[2]
    assert "INSERT INTO dimensions.dim_client" in insert_sql
    assert insert_params["secteur"] == "Pieces automobiles et electromobilite"


def test_load_dim_categorie_une_ligne_par_categorie_distincte():
    """load_dim_categorie insère une ligne par catégorie et construit le mapping libellé -> clé."""
    staging_conn = FakeStagingConnection([
        {"categorie": "Alimentaire"}, {"categorie": "Pieces auto"}, {"categorie": "Textile"},
    ])
    warehouse_conn = FakeWarehouseConnection()

    mapping = load_dim_categorie(staging_conn, warehouse_conn)

    assert set(mapping.keys()) == {"Alimentaire", "Pieces auto", "Textile"}
    assert len(warehouse_conn.cursor_obj.execute_calls) == 3


def test_client_categorie_keys_associe_un_client_a_une_categorie():
    """client_categorie_keys construit le mapping client_id -> categorie_key attendu."""
    staging_conn = FakeStagingConnection([
        {"client_id": 1, "categorie": "Pieces auto"},
        {"client_id": 2, "categorie": "Alimentaire"},
    ])
    categorie_keys = {"Pieces auto": 10, "Alimentaire": 20}

    mapping = client_categorie_keys(staging_conn, categorie_keys)

    assert mapping == {1: 10, 2: 20}


def test_client_categorie_keys_leve_une_erreur_si_client_multi_categories():
    """Un client avec des produits dans 2 catégories casse l'hypothèse vérifiée en C13."""
    staging_conn = FakeStagingConnection([
        {"client_id": 1, "categorie": "Pieces auto"},
        {"client_id": 1, "categorie": "Textile"},
    ])
    categorie_keys = {"Pieces auto": 10, "Textile": 30}

    with pytest.raises(ValueError, match="plusieurs catégories"):
        client_categorie_keys(staging_conn, categorie_keys)


def test_load_fait_stock_resout_les_cles_de_dimension():
    """load_fait_stock traduit entrepot_id/produit_id en site_key/produit_key et pose date_key."""
    staging_conn = FakeStagingConnection([
        {
            "entrepot_id": 2, "produit_id": 5, "quantite": 280,
            "date_maj": datetime.date(2026, 7, 29),
        },
    ])
    warehouse_conn = FakeWarehouseConnection()

    n = load_fait_stock(staging_conn, warehouse_conn, site_keys={2: 200}, produit_keys={5: 500})

    assert n == 1
    sql, records = warehouse_conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO exploitation.fait_stock" in sql
    assert records == [
        {"site_key": 200, "produit_key": 500, "date_key": 20260729, "quantite_stock": 280}
    ]


def test_load_fait_commande_calcule_le_poids_ligne():
    """load_fait_commande calcule poids_ligne = quantite x poids_kg et stringifie commande_id."""
    staging_conn = FakeStagingConnection([
        {
            "commande_id": 42, "client_id": 1, "entrepot_id": 2,
            "date_commande": datetime.date(2026, 7, 19), "statut": "Livree",
            "produit_id": 5, "quantite": 10, "poids_kg": 2.5,
        },
    ])
    warehouse_conn = FakeWarehouseConnection()

    n = load_fait_commande(
        staging_conn, warehouse_conn,
        client_keys={1: 100}, site_keys={2: 200}, produit_keys={5: 500},
    )

    assert n == 1
    sql, records = warehouse_conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO commercial.fait_commande" in sql
    (record,) = records
    assert record["commande_id"] == "42"
    assert record["quantite_commandee"] == 10
    assert record["poids_ligne"] == 25.0
    assert record["client_key"] == 100


def test_load_fait_commande_poids_ligne_none_si_poids_produit_inconnu():
    """Sans poids_kg produit renseigné, poids_ligne reste None plutôt qu'une erreur de calcul."""
    staging_conn = FakeStagingConnection([
        {
            "commande_id": 1, "client_id": 1, "entrepot_id": 2,
            "date_commande": datetime.date(2026, 1, 1), "statut": "Livree",
            "produit_id": 5, "quantite": 10, "poids_kg": None,
        },
    ])
    warehouse_conn = FakeWarehouseConnection()

    load_fait_commande(
        staging_conn, warehouse_conn,
        client_keys={1: 100}, site_keys={2: 200}, produit_keys={5: 500},
    )

    _, records = warehouse_conn.cursor_obj.executemany_calls[0]
    assert records[0]["poids_ligne"] is None


def test_load_fait_expedition_fluxpro_livree_a_lheure():
    """Une expédition livrée avant/à la date prévue est marquée livre_a_lheure=True."""
    staging_conn = FakeStagingConnection([
        {
            "tracking_number": "OMG0000001", "transporteur": "RapidFret",
            "date_expedition": datetime.date(2025, 12, 24),
            "date_livraison_prevue": datetime.date(2025, 12, 29),
            "date_livraison_reelle": datetime.date(2025, 12, 29),
            "statut": "Livree", "client_id": 1, "entrepot_id": 2, "poids_kg": 50.0,
        },
    ])
    warehouse_conn = FakeWarehouseConnection()

    n = load_fait_expedition_fluxpro(
        staging_conn, warehouse_conn,
        client_keys={1: 100}, site_keys={2: 200}, client_cat_keys={1: 300},
        transporteur_nom_keys={"RapidFret": 400},
    )

    assert n == 1
    _, records = warehouse_conn.cursor_obj.executemany_calls[0]
    (record,) = records
    assert record["livre_a_lheure"] is True
    assert record["delai_livraison_jours"] == 5
    assert record["source_systeme"] == "FluxPro_TransFlow"
    assert record["cout_transport_eur"] is None
    assert record["transporteur_key"] == 400


def test_load_fait_expedition_fluxpro_en_cours_champs_derives_none():
    """Une expédition non livrée (date_livraison_reelle NULL) laisse les champs dérivés à None."""
    staging_conn = FakeStagingConnection([
        {
            "tracking_number": "OMG0000002", "transporteur": "EcoRoute",
            "date_expedition": datetime.date(2026, 8, 1),
            "date_livraison_prevue": datetime.date(2026, 8, 6),
            "date_livraison_reelle": None,
            "statut": "Expediee", "client_id": 1, "entrepot_id": 2, "poids_kg": 12.0,
        },
    ])
    warehouse_conn = FakeWarehouseConnection()

    load_fait_expedition_fluxpro(
        staging_conn, warehouse_conn,
        client_keys={1: 100}, site_keys={2: 200}, client_cat_keys={1: 300},
        transporteur_nom_keys={"EcoRoute": 401},
    )

    _, records = warehouse_conn.cursor_obj.executemany_calls[0]
    (record,) = records
    assert record["livre_a_lheure"] is None
    assert record["delai_livraison_jours"] is None


def test_load_fait_expedition_historique_met_en_quarantaine_les_lignes_non_rapprochees():
    """Une ligne avec un client/entrepot/categorie inconnu est comptée en
    quarantaine, pas insérée."""
    staging_conn = FakeStagingConnection([
        {
            "client": "NordDrive", "entrepot": "Lyon", "categorie_produit": "Pieces auto",
            "date_expedition": datetime.date(2026, 1, 1), "poids_kg": 10.0,
            "delai_livraison_jours": 2, "cout_transport_eur": 15.0, "statut": "Livree",
        },
        {
            "client": "ClientInconnu", "entrepot": "Lyon", "categorie_produit": "Pieces auto",
            "date_expedition": datetime.date(2026, 1, 2), "poids_kg": 5.0,
            "delai_livraison_jours": 1, "cout_transport_eur": 8.0, "statut": "Livree",
        },
    ])
    warehouse_conn = FakeWarehouseConnection()

    n_inserees, n_quarantaine = load_fait_expedition_historique(
        staging_conn, warehouse_conn,
        client_nom_keys={"NordDrive": 100}, site_ville_keys={"Lyon": 200},
        categorie_keys={"Pieces auto": 300}, transporteur_inconnu_key=999,
    )

    assert n_inserees == 1
    assert n_quarantaine == 1
    _, records = warehouse_conn.cursor_obj.executemany_calls[0]
    assert len(records) == 1
    assert records[0]["source_systeme"] == "Historique"
    assert records[0]["transporteur_key"] == 999
    assert records[0]["livre_a_lheure"] is None
    assert records[0]["tracking_number"] is None
