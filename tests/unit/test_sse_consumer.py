"""Tests unitaires du consommateur SSE vers le data lake (C19)."""
import datetime
import json

from datacore.storage.lake.sse_consumer import consommer, evenements_depuis_lignes


class FakeS3Client:
    """Client S3 factice : enregistre les dépôts sans I/O réel."""

    def __init__(self):
        self.appels = []

    def put_object(self, Bucket, Key, Body):  # noqa: N803 (respecte la signature boto3)
        self.appels.append((Bucket, Key, Body))


class HorlogeFactice:
    """Horloge factice : avance d'une durée fixe à chaque appel (pas de vrai sleep en test)."""

    def __init__(self, depart, pas):
        self._maintenant = depart
        self._pas = pas

    def __call__(self):
        valeur = self._maintenant
        self._maintenant += self._pas
        return valeur


def _evenement(entrepot="OMG-LYO"):
    return f'data: {{"entrepot": "{entrepot}", "temperature_c": 3.5}}'


def test_evenements_depuis_lignes_ignore_les_lignes_vides_et_commentaires():
    """Seules les lignes `data: {...}` produisent un évènement."""
    lignes = ["", ": heartbeat", _evenement(), "", _evenement("OMG-LIL")]

    evenements = list(evenements_depuis_lignes(lignes))

    assert len(evenements) == 2
    assert evenements[0]["entrepot"] == "OMG-LYO"
    assert evenements[1]["entrepot"] == "OMG-LIL"


def test_evenements_depuis_lignes_decode_les_bytes():
    """Les lignes issues de `response.iter_lines()` sont des bytes, pas des str."""
    lignes = [_evenement().encode("utf-8")]

    evenements = list(evenements_depuis_lignes(lignes))

    assert evenements == [{"entrepot": "OMG-LYO", "temperature_c": 3.5}]


def test_consommer_deverse_a_chaque_intervalle_ecoule():
    """Un dépôt a lieu dès que l'intervalle est dépassé, pas seulement à la fin."""
    depart = datetime.datetime(2026, 9, 22, 10, 0, 0)
    horloge = HorlogeFactice(depart, datetime.timedelta(seconds=1))
    lignes = [_evenement() for _ in range(5)]
    s3 = FakeS3Client()

    cles = consommer(
        lignes, s3, bucket="omega-lake", intervalle=datetime.timedelta(seconds=2), horloge=horloge
    )

    # 5 evenements, horloge avance de 1s par evenement lu -> au moins 2 depots
    # (intervalle de 2s depasse plusieurs fois), plus le reliquat final.
    assert len(cles) >= 2
    assert len(s3.appels) == len(cles)


def test_consommer_ne_perd_aucun_evenement_entre_les_depots():
    """Le nombre total de lignes NDJSON déposées égale le nombre d'évènements reçus."""
    depart = datetime.datetime(2026, 9, 22, 10, 0, 0)
    horloge = HorlogeFactice(depart, datetime.timedelta(seconds=1))
    lignes = [_evenement() for _ in range(7)]
    s3 = FakeS3Client()

    consommer(
        lignes, s3, bucket="omega-lake", intervalle=datetime.timedelta(seconds=2), horloge=horloge
    )

    total_lignes_deposees = sum(body.decode("utf-8").count("\n") + 1 for _, _, body in s3.appels)
    assert total_lignes_deposees == 7


def test_consommer_partitionne_par_date_et_nomme_les_parts_de_facon_unique():
    """La clé S3 respecte raw/flux_sse_capteurs/date=.../part-<horodatage>.ndjson."""
    depart = datetime.datetime(2026, 9, 22, 10, 0, 0)
    horloge = HorlogeFactice(depart, datetime.timedelta(seconds=3))
    lignes = [_evenement()]
    s3 = FakeS3Client()

    cles = consommer(
        lignes, s3, bucket="omega-lake", intervalle=datetime.timedelta(seconds=1), horloge=horloge
    )

    assert len(cles) == 1
    assert cles[0].startswith("raw/flux_sse_capteurs/date=2026-09-22/part-")
    assert cles[0].endswith(".ndjson")


def test_consommer_respecte_duree_max():
    """`duree_max` arrête la consommation même si le flux (factice) a plus d'évènements."""
    depart = datetime.datetime(2026, 9, 22, 10, 0, 0)
    horloge = HorlogeFactice(depart, datetime.timedelta(seconds=1))
    lignes = [_evenement() for _ in range(100)]
    s3 = FakeS3Client()

    consommer(
        lignes,
        s3,
        bucket="omega-lake",
        intervalle=datetime.timedelta(seconds=1),
        horloge=horloge,
        duree_max=datetime.timedelta(seconds=5),
    )

    total_lignes_deposees = sum(body.decode("utf-8").count("\n") + 1 for _, _, body in s3.appels)
    assert total_lignes_deposees < 100


def test_deverser_ecrit_du_ndjson_valide():
    """Chaque ligne du contenu déposé est un JSON valide et fidèle à l'évènement d'origine."""
    depart = datetime.datetime(2026, 9, 22, 10, 0, 0)
    horloge = HorlogeFactice(depart, datetime.timedelta(seconds=10))
    lignes = [_evenement("OMG-LYO"), _evenement("OMG-MAR")]
    s3 = FakeS3Client()

    consommer(
        lignes, s3, bucket="omega-lake", intervalle=datetime.timedelta(seconds=100), horloge=horloge
    )

    _, _, body = s3.appels[0]
    lignes_decodees = [json.loads(ligne) for ligne in body.decode("utf-8").split("\n")]
    assert [e["entrepot"] for e in lignes_decodees] == ["OMG-LYO", "OMG-MAR"]
