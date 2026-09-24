"""Tests unitaires de l'ingestion batch des flux IoT vers le data lake (C19)."""
import datetime

from datacore.storage.lake.ingestion_batch import FLUX_BATCH, ingerer_flux_batch


class FakeS3Client:
    """Client S3 factice : enregistre les appels sans I/O réel (pas de MinIO en test)."""

    def __init__(self):
        self.appels = []

    def upload_file(self, chemin_local, bucket, cle):
        self.appels.append((chemin_local, bucket, cle))


def _creer_fichiers_iot(repertoire):
    """Crée les 4 fichiers batch attendus (contenu factice, seule l'existence compte)."""
    repertoire.mkdir(parents=True, exist_ok=True)
    for nom_fichier in FLUX_BATCH:
        (repertoire / nom_fichier).write_text("contenu factice")


def test_ingerer_flux_batch_depose_les_4_flux(tmp_path):
    """Les 4 flux batch sont chacun déposés une fois."""
    repertoire = tmp_path / "iot"
    _creer_fichiers_iot(repertoire)
    s3 = FakeS3Client()

    cles = ingerer_flux_batch(
        date_ingestion=datetime.date(2026, 9, 22), repertoire=repertoire, s3=s3
    )

    assert len(cles) == 4
    assert len(s3.appels) == 4


def test_ingerer_flux_batch_partitionne_par_date_ingestion(tmp_path):
    """La clé S3 porte la date d'ingestion, pas une date déduite du contenu."""
    repertoire = tmp_path / "iot"
    _creer_fichiers_iot(repertoire)
    s3 = FakeS3Client()

    cles = ingerer_flux_batch(
        date_ingestion=datetime.date(2026, 9, 22), repertoire=repertoire, s3=s3
    )

    assert "raw/capteurs_temperature/date=2026-09-22/capteurs_temperature.csv" in cles
    assert "raw/rfid_scans/date=2026-09-22/rfid_scans.json" in cles


def test_ingerer_flux_batch_transmet_bucket_et_chemin_local(tmp_path):
    """Chaque appel S3 pointe vers le bon fichier local et le bon bucket."""
    repertoire = tmp_path / "iot"
    _creer_fichiers_iot(repertoire)
    s3 = FakeS3Client()

    ingerer_flux_batch(date_ingestion=datetime.date(2026, 9, 22), repertoire=repertoire, s3=s3)

    chemin_local, bucket, cle = s3.appels[0]
    assert chemin_local == str(repertoire / "capteurs_temperature.csv")
    assert bucket == "omega-lake"
    assert cle.startswith("raw/capteurs_temperature/date=2026-09-22/")
