"""Tests unitaires du monitoring applicatif/matériel du data lake (C20bis).

Connexion Postgres remplacée par un fake (même pattern que
`test_load_dim_temps.py`) : ces tests vérifient la logique (ce qui est
envoyé en base), pas une vraie écriture -- ça, c'est le rôle de
`tests/integration/test_grafana_lake_monitoring.py`.
"""
import datetime

import pytest

from datacore.storage.lake.monitoring import (
    enregistrer_catalogue,
    enregistrer_purge,
    verifier_sante_infrastructure,
)


class FakeCursor:
    def __init__(self):
        self.executemany_calls = []
        self.execute_calls = []

    def executemany(self, sql, records):
        self.executemany_calls.append((sql, list(records)))

    def execute(self, sql, params):
        self.execute_calls.append((sql, params))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnectError(Exception):
    """Simule une panne de connexion Postgres (ex. base injoignable)."""


def _psycopg2_connect_leve_toujours(dsn):
    raise FakeConnectError("connexion refusée")


class FakePaginator:
    """Émule `boto3.client.get_paginator("list_objects_v2")` sur un jeu d'objets fixe.

    Trace le bucket réellement transmis par `paginate(Bucket=...)` --
    sans ça, un bug qui enverrait le mauvais bucket (ou aucun) à
    `verifier_sante_infrastructure()` passerait inaperçu.
    """

    def __init__(self, pages):
        self._pages = pages
        self.buckets_demandes = []

    def paginate(self, Bucket):  # noqa: N803
        self.buckets_demandes.append(Bucket)
        return self._pages


class FakeS3Accessible:
    def __init__(self):
        self.paginator = FakePaginator([
            {"Contents": [{"Size": 100}, {"Size": 250}]},
            {"Contents": [{"Size": 50}]},
        ])

    def get_paginator(self, nom):
        assert nom == "list_objects_v2"
        return self.paginator


class FakeS3Injoignable:
    def get_paginator(self, nom):
        raise ConnectionError("MinIO injoignable")


def test_enregistrer_catalogue_envoie_une_ligne_complete_par_entree(monkeypatch):
    """Chaque entrée du catalogue devient une ligne insérée dans monitoring.catalogue_lake --
    les deux entrées et tous leurs champs, pas seulement le début de la première."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.storage.lake.monitoring.psycopg2.connect", lambda dsn: conn)
    monkeypatch.setattr(
        "datacore.storage.lake.monitoring.construire_catalogue",
        lambda con, s3, bucket: [
            {"flux": "geoloc_flotte", "zone": "raw", "nb_lignes": 4320,
             "derniere_modification": "2026-09-24T14:55:00"},
            {"flux": "rfid_scans", "zone": "curated", "nb_lignes": 6000,
             "derniere_modification": "2026-09-24T14:55:01"},
        ],
    )

    n = enregistrer_catalogue(con_lake=None, s3=None, dsn="postgresql://fake")

    assert n == 2
    sql, records = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO monitoring.catalogue_lake" in sql
    assert len(records) == 2

    releve_le = records[0][4]
    assert records[0] == ("geoloc_flotte", "raw", 4320, "2026-09-24T14:55:00", releve_le)
    assert records[1] == ("rfid_scans", "curated", 6000, "2026-09-24T14:55:01", releve_le)


def test_enregistrer_purge_une_ligne_par_flux_meme_si_rien_purge(monkeypatch):
    """Un flux sans partition purgée produit quand même une ligne (0 partitions), pas d'omission."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.storage.lake.monitoring.psycopg2.connect", lambda dsn: conn)

    enregistrer_purge(
        {"geoloc_flotte": ["raw/geoloc_flotte/date=2026-01-01/x.csv"], "flux_sse_capteurs": []},
        dsn="postgresql://fake",
    )

    sql, records = conn.cursor_obj.executemany_calls[0]
    assert "INSERT INTO monitoring.purges_lake" in sql
    valeurs = {(flux, n) for flux, n, _ in records}
    assert valeurs == {("geoloc_flotte", 1), ("flux_sse_capteurs", 0)}


def test_verifier_sante_infrastructure_accessible_somme_les_tailles_du_bon_bucket(monkeypatch):
    """MinIO accessible : la capacité relevée est la somme réelle des tailles d'objets,
    et c'est bien le bucket demandé qui a été interrogé."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.storage.lake.monitoring.psycopg2.connect", lambda dsn: conn)
    s3 = FakeS3Accessible()

    resultat = verifier_sante_infrastructure(s3, dsn="postgresql://fake", bucket="mon-bucket")

    assert resultat == {"minio_accessible": True, "capacite_utilisee_octets": 400}
    assert s3.paginator.buckets_demandes == ["mon-bucket"]

    sql, params = conn.cursor_obj.execute_calls[0]
    accessible, capacite, releve_le = params
    assert (accessible, capacite) == (True, 400)
    assert isinstance(releve_le, datetime.datetime)


def test_verifier_sante_infrastructure_injoignable_nenleve_pas_lecriture(monkeypatch):
    """MinIO injoignable : enregistré comme tel (accessible=False), pas une exception qui
    ferait échouer tout le relevé -- c'est justement l'état à détecter, pas une erreur du
    monitoring lui-même."""
    conn = FakeConnection()
    monkeypatch.setattr("datacore.storage.lake.monitoring.psycopg2.connect", lambda dsn: conn)

    resultat = verifier_sante_infrastructure(FakeS3Injoignable(), dsn="postgresql://fake")

    assert resultat == {"minio_accessible": False, "capacite_utilisee_octets": None}
    sql, params = conn.cursor_obj.execute_calls[0]
    assert params[0] is False
    assert params[1] is None


def test_verifier_sante_infrastructure_panne_postgres_nest_pas_avalee(monkeypatch):
    """Contrairement à une panne MinIO (l'état mesuré lui-même), une panne de la connexion
    Postgres n'est pas interceptée -- elle remonte telle quelle, même principe que
    `journal.py::journaliser()` ("la journalisation observe, elle n'avale jamais une erreur
    réelle"). Documenté ici pour que ce comportement reste intentionnel, pas un oubli."""
    monkeypatch.setattr(
        "datacore.storage.lake.monitoring.psycopg2.connect", _psycopg2_connect_leve_toujours
    )

    with pytest.raises(FakeConnectError):
        verifier_sante_infrastructure(FakeS3Accessible(), dsn="postgresql://fake")


def test_enregistrer_catalogue_panne_postgres_nest_pas_avalee(monkeypatch):
    """Même principe que ci-dessus, côté enregistrer_catalogue()."""
    monkeypatch.setattr(
        "datacore.storage.lake.monitoring.psycopg2.connect", _psycopg2_connect_leve_toujours
    )
    monkeypatch.setattr(
        "datacore.storage.lake.monitoring.construire_catalogue",
        lambda con, s3, bucket: [
            {"flux": "geoloc_flotte", "zone": "raw", "nb_lignes": 1,
             "derniere_modification": "2026-09-24T14:55:00"},
        ],
    )

    with pytest.raises(FakeConnectError):
        enregistrer_catalogue(con_lake=None, s3=None, dsn="postgresql://fake")
