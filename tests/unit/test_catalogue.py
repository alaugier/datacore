"""Tests unitaires du catalogue automatisé du data lake (C20)."""
import datetime

from datacore.storage.lake.catalogue import FLUX, ZONES, catalogue_entree, construire_catalogue


class FakeS3Client:
    """Client S3 factice : sert des objets préconfigurés par préfixe."""

    def __init__(self, objets_par_prefixe):
        self._objets = objets_par_prefixe

    def list_objects_v2(self, Bucket, Prefix, MaxKeys=None):  # noqa: N803
        objets = self._objets.get(Prefix, [])
        if MaxKeys is not None:
            objets = objets[:MaxKeys]
        reponse = {"KeyCount": len(objets)}
        if objets:
            reponse["Contents"] = objets
        return reponse


class FakeResultat:
    """Résultat factice imitant l'API DuckDBPyRelation utilisée ici."""

    def __init__(self, valeur):
        self._valeur = valeur

    def fetchall(self):
        return self._valeur

    def fetchone(self):
        return self._valeur


class FakeCon:
    """Connexion DuckDB factice : DESCRIBE renvoie un schéma fixe, le reste un compte fixe."""

    def __init__(self, schema, nb_lignes):
        self._schema = schema
        self._nb_lignes = nb_lignes
        self.requetes = []

    def sql(self, requete):
        self.requetes.append(requete)
        if requete.strip().startswith("DESCRIBE"):
            return FakeResultat(self._schema)
        return FakeResultat((self._nb_lignes,))


def test_catalogue_entree_absente_renvoie_none_sans_interroger_duckdb():
    """Aucun objet pour ce flux/zone : pas d'introspection, juste None."""
    s3 = FakeS3Client({})
    con = FakeCon(schema=[], nb_lignes=0)

    entree = catalogue_entree(con, s3, "capteurs_temperature", "curated", "omega-lake")

    assert entree is None
    assert con.requetes == []


def test_catalogue_entree_construit_le_bon_dict():
    """Une entrée existante produit source/zone/format/schéma/nb_lignes/fraîcheur."""
    horodatage = datetime.datetime(2026, 9, 23, 8, 27, 41, tzinfo=datetime.UTC)
    s3 = FakeS3Client(
        {
            "curated/capteurs_temperature/": [{"LastModified": horodatage}],
        }
    )
    schema = [("timestamp", "TIMESTAMP"), ("entrepot", "VARCHAR"), ("entrepot_nom", "VARCHAR")]
    con = FakeCon(schema=schema, nb_lignes=2592)

    entree = catalogue_entree(con, s3, "capteurs_temperature", "curated", "omega-lake")

    assert entree["flux"] == "capteurs_temperature"
    assert entree["zone"] == "curated"
    assert entree["format"] == "parquet"
    assert entree["nb_lignes"] == 2592
    assert entree["derniere_modification"] == horodatage.isoformat()
    assert entree["schema"] == [
        {"colonne": "timestamp", "type": "TIMESTAMP"},
        {"colonne": "entrepot", "type": "VARCHAR"},
        {"colonne": "entrepot_nom", "type": "VARCHAR"},
    ]


def test_catalogue_entree_format_raw_reflete_le_format_source():
    """En zone raw/, le format est celui du fichier source, pas toujours Parquet."""
    horodatage = datetime.datetime(2026, 9, 23, tzinfo=datetime.UTC)
    s3 = FakeS3Client({"raw/rfid_scans/": [{"LastModified": horodatage}]})
    con = FakeCon(schema=[("scan_id", "BIGINT")], nb_lignes=3000)

    entree = catalogue_entree(con, s3, "rfid_scans", "raw", "omega-lake")

    assert entree["format"] == "json"


def test_construire_catalogue_omet_les_flux_zones_sans_contenu():
    """Seules les combinaisons flux/zone réellement présentes sont cataloguées."""
    horodatage = datetime.datetime(2026, 9, 23, tzinfo=datetime.UTC)
    # Un seul flux/une seule zone alimentée, sur les 5 x 3 = 15 combinaisons possibles.
    s3 = FakeS3Client({"curated/rfid_scans/": [{"LastModified": horodatage}]})
    con = FakeCon(schema=[("scan_id", "BIGINT")], nb_lignes=3000)

    catalogue = construire_catalogue(con, s3, "omega-lake")

    assert len(catalogue) == 1
    assert catalogue[0]["flux"] == "rfid_scans"
    assert catalogue[0]["zone"] == "curated"


def test_flux_et_zones_couvrent_bien_les_5_flux_et_3_zones_attendues():
    """Garde-fou : la couverture nominale reste 5 flux x 3 zones = 15 combinaisons."""
    assert len(FLUX) == 5
    assert ZONES == ("raw", "staging", "curated")
