"""Tests unitaires de la purge RGPD des flux de géolocalisation (C21)."""
import datetime

from datacore.storage.lake.purge import partitions_a_purger, purger_geolocalisation


class FakeS3Client:
    """Client S3 factice : sert des objets préconfigurés par préfixe, supprime réellement."""

    def __init__(self, objets_par_prefixe):
        self._objets = {k: list(v) for k, v in objets_par_prefixe.items()}
        self.supprimes = []

    def list_objects_v2(self, Bucket, Prefix, MaxKeys=None):  # noqa: N803
        objets = [o for o in self._objets.get(Prefix, []) if o["Key"] not in self.supprimes]
        reponse = {"KeyCount": len(objets)}
        if objets:
            reponse["Contents"] = objets
        return reponse

    def delete_object(self, Bucket, Key):  # noqa: N803
        self.supprimes.append(Key)


class FakeCon:
    """Connexion DuckDB factice : n'exécute rien pour de vrai, trace seulement les appels."""

    def __init__(self):
        self.appels = []

    def sql(self, requete):
        self.appels.append(requete)


def test_partitions_a_purger_ne_retient_que_les_partitions_trop_anciennes():
    """Seules les partitions antérieures à l'horizon de rétention sont listées."""
    aujourdhui = datetime.date(2026, 9, 23)
    s3 = FakeS3Client(
        {
            "raw/geoloc_flotte/": [
                {"Key": "raw/geoloc_flotte/date=2026-09-23/geoloc_flotte.csv"},  # aujourd'hui
                {"Key": "raw/geoloc_flotte/date=2026-06-01/geoloc_flotte.csv"},  # ancien (>90j)
            ]
        }
    )

    cles = partitions_a_purger(s3, "geoloc_flotte", bucket="omega-lake", aujourdhui=aujourdhui)

    assert cles == ["raw/geoloc_flotte/date=2026-06-01/geoloc_flotte.csv"]


def test_partitions_a_purger_respecte_lhorizon_parametre():
    """Un horizon de rétention plus court purge davantage de partitions."""
    aujourdhui = datetime.date(2026, 9, 23)
    s3 = FakeS3Client(
        {
            "raw/geoloc_flotte/": [
                {"Key": "raw/geoloc_flotte/date=2026-09-20/geoloc_flotte.csv"},  # il y a 3 jours
            ]
        }
    )

    assert partitions_a_purger(
        s3, "geoloc_flotte", bucket="omega-lake", horizon_jours=90, aujourdhui=aujourdhui
    ) == []
    assert partitions_a_purger(
        s3, "geoloc_flotte", bucket="omega-lake", horizon_jours=1, aujourdhui=aujourdhui
    ) == ["raw/geoloc_flotte/date=2026-09-20/geoloc_flotte.csv"]


def test_purger_geolocalisation_supprime_reellement_les_cles_identifiees():
    """purger_geolocalisation() appelle bien delete_object sur chaque partition ancienne."""
    aujourdhui = datetime.date(2026, 9, 23)
    s3 = FakeS3Client(
        {
            "raw/geoloc_flotte/": [
                {"Key": "raw/geoloc_flotte/date=2026-09-23/geoloc_flotte.csv"},
                {"Key": "raw/geoloc_flotte/date=2026-01-01/geoloc_flotte.csv"},
            ],
            "raw/flux_sse_capteurs/": [
                {"Key": "raw/flux_sse_capteurs/date=2026-09-23/part-0.ndjson"},
            ],
        }
    )
    con = FakeCon()

    resultat = purger_geolocalisation(s3, con, bucket="omega-lake", aujourdhui=aujourdhui)

    assert resultat["geoloc_flotte"] == ["raw/geoloc_flotte/date=2026-01-01/geoloc_flotte.csv"]
    assert resultat["flux_sse_capteurs"] == []
    assert s3.supprimes == ["raw/geoloc_flotte/date=2026-01-01/geoloc_flotte.csv"]


def test_purger_geolocalisation_reconstruit_staging_curated_si_des_partitions_subsistent():
    """Après purge, staging/curated sont régénérés uniquement pour le flux effectivement purgé."""
    aujourdhui = datetime.date(2026, 9, 23)
    s3 = FakeS3Client(
        {
            "raw/geoloc_flotte/": [
                {"Key": "raw/geoloc_flotte/date=2026-09-23/geoloc_flotte.csv"},
                {"Key": "raw/geoloc_flotte/date=2026-01-01/geoloc_flotte.csv"},
            ],
            "raw/flux_sse_capteurs/": [
                {"Key": "raw/flux_sse_capteurs/date=2026-09-23/part-0.ndjson"},
            ],
        }
    )
    con = FakeCon()

    purger_geolocalisation(s3, con, bucket="omega-lake", aujourdhui=aujourdhui)

    # geoloc_flotte a ete purge -> reconstruction attendue (2 requetes : staging + curated).
    requetes_geoloc = [r for r in con.appels if "geoloc_flotte" in r]
    assert len(requetes_geoloc) == 2
    # flux_sse_capteurs n'a rien eu a purger -> aucune reconstruction inutile.
    assert not any("flux_sse_capteurs" in r for r in con.appels)


def test_purger_geolocalisation_ne_purge_pas_les_flux_non_concernes():
    """Seuls geoloc_flotte et flux_sse_capteurs sont visés -- pas capteurs_temperature."""
    aujourdhui = datetime.date(2026, 9, 23)
    s3 = FakeS3Client({})
    con = FakeCon()

    resultat = purger_geolocalisation(s3, con, bucket="omega-lake", aujourdhui=aujourdhui)

    assert set(resultat.keys()) == {"geoloc_flotte", "flux_sse_capteurs"}
