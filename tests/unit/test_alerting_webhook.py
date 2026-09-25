"""Tests unitaires du relais d'alerte Grafana -> e-mail (C20bis).

`smtplib.SMTP` est remplacé par un fake (aucun envoi réseau réel) --
l'envoi réel vers MailHog est vérifié dans
`tests/integration/test_grafana_lake_monitoring.py`.
"""
import pytest

from datacore.alerting.webhook import _resumer_payload, app, envoyer_alerte


class FakeSMTP:
    """Remplace `smtplib.SMTP` : trace les messages envoyés sans réseau."""

    messages_envoyes: list = []

    def __init__(self, hote, port):
        self.hote = hote
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def send_message(self, message):
        FakeSMTP.messages_envoyes.append(message)


@pytest.fixture(autouse=True)
def _reset_fake_smtp():
    FakeSMTP.messages_envoyes = []
    yield


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_resumer_payload_avec_une_alerte():
    payload = {
        "status": "firing",
        "alerts": [
            {
                "labels": {"alertname": "MinIOInjoignable"},
                "annotations": {"summary": "MinIO ne répond plus"},
            }
        ],
    }
    sujet, corps = _resumer_payload(payload)
    assert "firing" in sujet
    assert "MinIOInjoignable" in sujet
    assert "MinIO ne répond plus" in corps


def test_resumer_payload_sans_alerte_ne_leve_pas_derreur():
    """Un payload inattendu (pas de clé `alerts`) retombe sur un résumé générique,
    plutôt qu'une exception qui ferait échouer le relais de l'alerte elle-même."""
    sujet, corps = _resumer_payload({"status": "ok"})
    assert "ok" in sujet
    assert corps


def test_envoyer_alerte_envoie_un_message_smtp(monkeypatch):
    monkeypatch.setattr("datacore.alerting.webhook.smtplib.SMTP", FakeSMTP)

    envoyer_alerte("sujet de test", "corps de test", hote_smtp="fake-host", port_smtp=1025)

    assert len(FakeSMTP.messages_envoyes) == 1
    message = FakeSMTP.messages_envoyes[0]
    assert message["Subject"] == "sujet de test"
    assert message.get_content().strip() == "corps de test"


def test_route_webhook_alertes_relaie_un_email(client, monkeypatch):
    monkeypatch.setattr("datacore.alerting.webhook.smtplib.SMTP", FakeSMTP)

    reponse = client.post(
        "/webhook/alertes",
        json={
            "status": "firing",
            "alerts": [
                {"labels": {"alertname": "TestAlerte"}, "annotations": {"summary": "résumé"}}
            ],
        },
    )

    assert reponse.status_code == 200
    assert len(FakeSMTP.messages_envoyes) == 1
    assert "TestAlerte" in FakeSMTP.messages_envoyes[0]["Subject"]


def test_route_health_sans_authentification(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.get_json()["status"] == "ok"
