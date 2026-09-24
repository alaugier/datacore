"""Tests unitaires de la détection de colonnes évoquant une donnée personnelle (C16, C21).

`colonnes_suspectes` est une fonction pure, testée sans dépendance à une
base réelle. `auditer` (introspection SQL) et `auditer_lake`
(introspection du catalogue du data lake) sont vérifiées pour de vrai
contre une infrastructure réelle (Docker Compose), documentées
respectivement dans `docs/architecture/registre_rgpd_entrepot.md` et
`docs/architecture/registre_rgpd_lake.md`.
"""
from datacore.governance.audit_rgpd import auditer_lake, colonnes_suspectes


def test_detecte_les_colonnes_personnelles_connues():
    """Les 3 colonnes personnelles déjà identifiées en C11 sont bien détectées."""
    colonnes = ["id", "chauffeur", "adresse_livraison", "contact", "date"]

    assert colonnes_suspectes(colonnes) == ["chauffeur", "adresse_livraison", "contact"]


def test_ne_signale_pas_les_noms_dentreprise():
    """nom/libelle/code (client, site, transporteur, catégorie) ne sont pas des personnes."""
    colonnes = ["client_key", "nom", "code", "libelle", "secteur", "ville"]

    assert colonnes_suspectes(colonnes) == []


def test_detecte_insensible_a_la_casse():
    """La détection ne dépend pas de la casse du nom de colonne."""
    assert colonnes_suspectes(["CHAUFFEUR", "Adresse_Livraison"]) == [
        "CHAUFFEUR", "Adresse_Livraison",
    ]


def test_liste_vide_sans_colonne_suspecte():
    """Aucune colonne suspecte : liste vide, pas d'erreur."""
    assert colonnes_suspectes([]) == []


class FakeS3Client:
    """Client S3 factice : un seul objet par préfixe demandé, avec LastModified."""

    def __init__(self, prefixes_peuples):
        self._prefixes = prefixes_peuples

    def list_objects_v2(self, Bucket, Prefix, MaxKeys=None):  # noqa: N803
        import datetime

        if Prefix not in self._prefixes:
            return {"KeyCount": 0}
        return {
            "KeyCount": 1,
            "Contents": [{"LastModified": datetime.datetime(2026, 9, 23, tzinfo=datetime.UTC)}],
        }


class FakeResultat:
    """Résultat factice imitant l'API DuckDBPyRelation utilisée ici."""

    def __init__(self, valeur):
        self._valeur = valeur

    def fetchall(self):
        return self._valeur

    def fetchone(self):
        return self._valeur


class FakeCon:
    """Connexion DuckDB factice : renvoie un schéma fixe pour DESCRIBE, un compte fixe sinon."""

    def __init__(self, schema):
        self._schema = schema

    def sql(self, requete):
        if requete.strip().startswith("DESCRIBE"):
            return FakeResultat(self._schema)
        return FakeResultat((1,))


def test_auditer_lake_detecte_une_colonne_suspecte_dans_le_catalogue():
    """Une colonne évoquant une donnée personnelle dans le schéma d'un flux est signalée."""
    s3 = FakeS3Client({"curated/geoloc_flotte/": True})
    con = FakeCon(schema=[("vehicule_id", "VARCHAR"), ("chauffeur_nom", "VARCHAR")])

    resultat = auditer_lake(con, s3, bucket="omega-lake")

    assert resultat == {"curated/geoloc_flotte": ["chauffeur_nom"]}


def test_auditer_lake_ne_signale_rien_sur_un_schema_propre():
    """Schéma réel connu (entrepot, produit_sku, ...), aucune colonne suspecte : rien signalé."""
    s3 = FakeS3Client({"curated/rfid_scans/": True})
    con = FakeCon(
        schema=[("scan_id", "BIGINT"), ("entrepot", "VARCHAR"), ("produit_sku", "VARCHAR")]
    )

    assert auditer_lake(con, s3, bucket="omega-lake") == {}
