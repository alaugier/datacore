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

from datacore.config import (
    ALERTING_WEBHOOK_PORT,
    ALERTING_WEBHOOK_SECRET,
    GRAFANA_ADMIN_PASSWORD,
    GRAFANA_ADMIN_USER,
    GRAFANA_PORT,
    MAILHOG_API_PORT,
)

GRAFANA_URL = f"http://localhost:{GRAFANA_PORT}"
ALERTING_WEBHOOK_URL = f"http://localhost:{ALERTING_WEBHOOK_PORT}"
AUTH = (GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD)


def _infra_disponible(hote: str, port: int, delai: float = 1.0) -> bool:
    try:
        with socket.create_connection((hote, port), timeout=delai):
            return True
    except OSError:
        return False


_grafana_ok = _infra_disponible("localhost", int(GRAFANA_PORT))
_minio_ok = _infra_disponible("localhost", 9000)
_alerting_ok = _infra_disponible("localhost", int(ALERTING_WEBHOOK_PORT))
_mailhog_ok = _infra_disponible("localhost", int(MAILHOG_API_PORT))

pytestmark = pytest.mark.skipif(
    not (_grafana_ok and _minio_ok and _alerting_ok and _mailhog_ok),
    reason=(
        "Grafana/MinIO/alerting-webhook/MailHog non accessibles -- lancer "
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


def test_dashboard_monitoring_lake_provisionne_avec_ses_6_panels():
    """4 panels initiaux + débit SSE (série temporelle) + scraping (table), issue #104."""
    url = f"{GRAFANA_URL}/api/dashboards/uid/monitoring-lake"
    reponse = requests.get(url, auth=AUTH, timeout=5)
    assert reponse.status_code == 200
    panels = reponse.json()["dashboard"]["panels"]
    assert len(panels) == 6


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
    assert webhook["settings"]["headers"]["X-Webhook-Secret"] == ALERTING_WEBHOOK_SECRET
    assert webhook["provenance"] == "file"


def test_alerting_webhook_reel_refuse_sans_le_bon_secret():
    """Le conteneur alerting-webhook réel (pas un test client Flask en mémoire) applique
    bien l'authentification -- le port est exposé sur l'hôte (docker-compose.yml)."""
    payload = {"status": "firing", "alerts": []}

    sans_secret = requests.post(f"{ALERTING_WEBHOOK_URL}/webhook/alertes", json=payload, timeout=5)
    assert sans_secret.status_code == 401

    bon_secret = requests.post(
        f"{ALERTING_WEBHOOK_URL}/webhook/alertes",
        json=payload,
        headers={"X-Webhook-Secret": ALERTING_WEBHOOK_SECRET},
        timeout=5,
    )
    assert bon_secret.status_code == 200


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


def test_releve_sse_recent_est_bien_dans_la_fenetre_timefilter_de_grafana():
    """Non-régression (issue #104, trouvé en répétition) : un relevé fait
    "maintenant" doit tomber dans la fenêtre `$__timeFilter` de Grafana.

    `monitoring.debit_flux_sse.releve_le` est un TIMESTAMP sans fuseau,
    comparé en UTC par `$__timeFilter` -- écrire en heure locale (CET)
    le faisait paraître dans le futur par rapport au `now` UTC de
    Grafana, et il sortait silencieusement de toute fenêtre récente
    (voir `monitoring._maintenant_utc()`).
    """
    import datetime

    import psycopg2

    from datacore.config import OMEGA_BI_DB_DSN
    from datacore.storage.lake.monitoring import enregistrer_evenements_fenetre

    flux_test = "flux_test_non_regression_utc"
    releve_le = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    enregistrer_evenements_fenetre(flux_test, 1, releve_le)
    try:
        reponse = requests.post(
            f"{GRAFANA_URL}/api/ds/query",
            auth=AUTH,
            json={
                "queries": [{
                    "refId": "A",
                    "datasource": {"type": "postgres", "uid": "omega_bi_reader"},
                    "rawSql": (
                        "SELECT releve_le AS \"time\", nb_evenements FROM monitoring.debit_flux_sse "
                        f"WHERE flux = '{flux_test}' AND $__timeFilter(releve_le)"
                    ),
                    "format": "time_series",
                }],
                "from": "now-5m",
                "to": "now",
            },
            timeout=5,
        )
        reponse.raise_for_status()
        valeurs = reponse.json()["results"]["A"]["frames"][0]["data"]["values"]
        assert valeurs and valeurs[0], (
            "le relevé vient d'être écrit mais n'apparaît pas dans la fenêtre now-5m/now"
        )
    finally:
        # Nettoyage : ce relevé de test ne doit pas polluer le panel Grafana
        # réel (sa requête n'a pas de filtre sur `flux`, voir le dashboard).
        with psycopg2.connect(OMEGA_BI_DB_DSN) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM monitoring.debit_flux_sse WHERE flux = %s", (flux_test,))


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
