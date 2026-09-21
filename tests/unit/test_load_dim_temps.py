"""Tests unitaires du chargeur de la dimension calendaire (C14).

`generer_lignes` est testée en pure logique (aucune dépendance base de
données) ; `charger_dim_temps` avec une connexion/curseur factices, sur
le même principe que `tests/unit/test_load_staging.py`.
"""
import datetime

import pytest

from datacore.storage.warehouse.load_dim_temps import charger_dim_temps, generer_lignes


def test_generer_lignes_couvre_toute_la_plage_incluse():
    """Une ligne par jour, bornes incluses."""
    lignes = generer_lignes(datetime.date(2026, 1, 1), datetime.date(2026, 1, 3))

    assert len(lignes) == 3
    assert [ligne[1] for ligne in lignes] == [
        datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 2),
        datetime.date(2026, 1, 3),
    ]


def test_generer_lignes_date_key_est_yyyymmdd():
    """date_key est l'entier YYYYMMDD correspondant à la date."""
    (ligne,) = generer_lignes(datetime.date(2026, 8, 28), datetime.date(2026, 8, 28))

    date_key, date_complete = ligne[0], ligne[1]
    assert date_key == 20260828
    assert date_complete == datetime.date(2026, 8, 28)


def test_generer_lignes_annee_trimestre_mois():
    """Les attributs calendaires dérivés correspondent à la date."""
    (ligne,) = generer_lignes(datetime.date(2026, 8, 28), datetime.date(2026, 8, 28))

    _, _, annee, trimestre, mois, nom_mois, *_ = ligne
    assert annee == 2026
    assert trimestre == 3
    assert mois == 8
    assert nom_mois == "Aout"


def test_generer_lignes_est_weekend_correct():
    """Vendredi 28/08/2026 n'est pas un weekend, samedi 29/08/2026 en est un."""
    lignes = generer_lignes(datetime.date(2026, 8, 28), datetime.date(2026, 8, 29))

    vendredi, samedi = lignes
    assert vendredi[-1] is False
    assert samedi[-1] is True


def test_generer_lignes_rejette_une_plage_inversee():
    """date_debut postérieure à date_fin lève une erreur explicite plutôt qu'une liste vide."""
    with pytest.raises(ValueError):
        generer_lignes(datetime.date(2026, 1, 3), datetime.date(2026, 1, 1))


class FakeCursor:
    """Curseur factice : enregistre les appels executemany reçus.

    Args:
        rowcount_insere: valeur simulée de `cur.rowcount` après
            `executemany` — par défaut égale au nombre d'enregistrements
            envoyés (aucun conflit), surchargeable pour simuler des
            lignes ignorées par `ON CONFLICT DO NOTHING`.
    """

    def __init__(self, rowcount_insere=None):
        self.executemany_calls = []
        self._rowcount_insere = rowcount_insere
        self.rowcount = 0

    def executemany(self, sql, records):
        records = list(records)
        self.executemany_calls.append((sql, records))
        self.rowcount = (
            self._rowcount_insere if self._rowcount_insere is not None else len(records)
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    """Connexion factice supportant le protocole context manager utilisé par charger_dim_temps."""

    def __init__(self, cursor_obj=None):
        self.cursor_obj = cursor_obj or FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_charger_dim_temps_insere_et_commit(monkeypatch):
    """charger_dim_temps envoie un executemany avec ON CONFLICT et commit."""
    conn = FakeConnection()
    monkeypatch.setattr(
        "datacore.storage.warehouse.load_dim_temps.psycopg2.connect", lambda dsn: conn
    )

    n = charger_dim_temps(dsn="postgresql://fake")

    assert n > 0
    sql, records = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO dimensions.dim_temps" in sql
    assert "ON CONFLICT (date_key) DO NOTHING" in sql
    assert len(records) == n
    assert conn.committed is True


def test_charger_dim_temps_retourne_rowcount_pas_le_nombre_envoye(monkeypatch):
    """Le retour reflète les lignes réellement insérées (cur.rowcount), pas celles envoyées.

    Simule un ON CONFLICT qui ignore une partie des lignes (ex. un
    second chargement partiellement recouvrant) : le nombre de lignes
    générées est le même, mais rowcount, lui, diffère.
    """
    conn = FakeConnection(cursor_obj=FakeCursor(rowcount_insere=1))
    monkeypatch.setattr(
        "datacore.storage.warehouse.load_dim_temps.psycopg2.connect", lambda dsn: conn
    )

    n = charger_dim_temps(dsn="postgresql://fake")

    sql, records = conn.cursor_obj.executemany_calls[0]
    assert len(records) > 1  # des lignes ont bien été envoyées...
    assert n == 1  # ...mais seule une a été réellement insérée
