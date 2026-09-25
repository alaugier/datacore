"""Test d'intégration du monitoring du data lake dans Grafana (C20bis).

Vérifie que le provisioning (dashboard, source de données, alerte) est
réel et que les relevés de `datacore.storage.lake.monitoring`
atterrissent bien dans les tables interrogées par Grafana.

**La coupure réelle de MinIO n'est pas automatisée ici** (même
précédent que le test `kill -9` du consommateur SSE, C19 -- voir
`docs/architecture/integration_infrastructure_omega_lake.md` §3) :
arrêter un conteneur depuis la suite de tests serait invasif et
fragiliserait le reste de la suite. Cette vérification a été faite une
fois, manuellement, en conditions réelles, et documentée avec preuves
dans `docs/architecture/gestion_operationnelle_omega_bi.md`.

**Ignoré (skip), pas échoué, si l'infrastructure n'est pas démarrée** :

    docker compose -f infra/docker/docker-compose.yml --env-file .env \\
        up -d db minio minio-init grafana alerting-webhook mailhog
    pytest tests/integration/test_grafana_lake_monitoring.py -v
"""
import socket

import pytest
import requests

from datacore.config import GRAFANA_ADMIN_PASSWORD, GRAFANA_ADMIN_USER, GRAFANA_PORT

GRAFANA_URL = f"http://localhost:{GRAFANA_PORT}"
AUTH = (GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD)


def _infra_disponible(hote: str, port: int, delai: float = 1.0) -> bool:
    try:
        with socket.create_connection((hote, port), timeout=delai):
            return True
    except OSError:
        return False


_grafana_ok = _infra_disponible("localhost", int(GRAFANA_PORT))
_minio_ok = _infra_disponible("localhost", 9000)

pytestmark = pytest.mark.skipif(
    not (_grafana_ok and _minio_ok),
    reason=(
        "Grafana/MinIO non accessibles -- lancer "
        "`docker compose -f infra/docker/docker-compose.yml --env-file .env "
        "up -d db minio minio-init grafana alerting-webhook mailhog` avant ce test"
    ),
)


@pytest.fixture(scope="module")
def releves():
    """Exécute pour de vrai les relevés catalogue + santé infra une fois pour le module."""
    from datacore.storage.lake.ingestion_batch import client
    from datacore.storage.lake.monitoring import (
        enregistrer_catalogue,
        verifier_sante_infrastructure,
    )
    from datacore.storage.lake.transform import connexion

    s3 = client()
    con = connexion()
    nb_entrees = enregistrer_catalogue(con, s3)
    sante = verifier_sante_infrastructure(s3)
    return {"nb_entrees_catalogue": nb_entrees, "sante": sante}


def test_dashboard_monitoring_lake_provisionne_avec_ses_4_panels():
    url = f"{GRAFANA_URL}/api/dashboards/uid/monitoring-lake"
    reponse = requests.get(url, auth=AUTH, timeout=5)
    assert reponse.status_code == 200
    panels = reponse.json()["dashboard"]["panels"]
    assert len(panels) == 4


def test_point_de_contact_webhook_alerting_provisionne():
    """Le point de contact vers alerting-webhook est bien celui utilisé par l'alerte --
    pas configuré à la main dans l'UI (provenance "file")."""
    url = f"{GRAFANA_URL}/api/v1/provisioning/contact-points"
    reponse = requests.get(url, auth=AUTH, timeout=5)
    assert reponse.status_code == 200
    points = reponse.json()
    webhook = next(p for p in points if p["uid"] == "alerting_webhook_receiver")
    assert webhook["type"] == "webhook"
    assert webhook["settings"]["url"] == "http://alerting-webhook:5060/webhook/alertes"
    assert webhook["provenance"] == "file"


def test_regle_dalerte_minio_injoignable_provisionnee():
    reponse = requests.get(f"{GRAFANA_URL}/api/v1/provisioning/alert-rules", auth=AUTH, timeout=5)
    assert reponse.status_code == 200
    regles = {r["uid"]: r for r in reponse.json()}
    assert "minio_injoignable" in regles


def test_releve_catalogue_atterrit_dans_postgres_et_est_interrogeable(releves):
    assert releves["nb_entrees_catalogue"] > 0

    reponse = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        auth=AUTH,
        json={
            "queries": [{
                "refId": "A",
                "datasource": {"type": "postgres", "uid": "omega_bi_reader"},
                "rawSql": "SELECT count(*) AS n FROM monitoring.catalogue_lake",
                "format": "table",
            }]
        },
        timeout=5,
    )
    reponse.raise_for_status()
    n = reponse.json()["results"]["A"]["frames"][0]["data"]["values"][0][0]
    assert n >= releves["nb_entrees_catalogue"]


def test_releve_sante_infrastructure_reflete_letat_reel_de_minio(releves):
    """Au moment de ce test, MinIO est accessible (précondition de skip du module) --
    le relevé doit donc l'enregistrer comme tel."""
    assert releves["sante"]["minio_accessible"] is True
    assert releves["sante"]["capacite_utilisee_octets"] is not None


def test_bi_reader_peut_lire_le_schema_monitoring():
    """Le schéma `monitoring` est bien accessible à bi_reader (C14/C20bis) -- pas
    seulement exploitation/dimensions/commercial."""
    reponse = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        auth=AUTH,
        json={
            "queries": [{
                "refId": "A",
                "datasource": {"type": "postgres", "uid": "omega_bi_reader"},
                "rawSql": "SELECT 1 FROM monitoring.sante_infrastructure LIMIT 1",
                "format": "table",
            }]
        },
        timeout=5,
    )
    assert reponse.status_code == 200
    assert reponse.json()["results"]["A"]["status"] == 200
