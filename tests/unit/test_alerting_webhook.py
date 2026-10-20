"""Tests unitaires du relais d'alerte Grafana -> e-mail (C20bis).

`smtplib.SMTP` est remplacé par un fake (aucun envoi réseau réel) --
l'envoi réel vers MailHog est vérifié dans
`tests/integration/test_grafana_lake_monitoring.py`.
"""
import smtplib

import pytest

from datacore.alerting.webhook import (
    DESTINATAIRE,
    EXPEDITEUR,
    _resumer_payload,
    app,
    envoyer_alerte,
)
from datacore.config import ALERTING_WEBHOOK_SECRET

EN_TETES_VALIDES = {"X-Webhook-Secret": ALERTING_WEBHOOK_SECRET}


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


class FakeSMTPEnPanne:
    """Remplace `smtplib.SMTP` par une connexion qui échoue toujours (serveur injoignable)."""

    def __init__(self, hote, port):
        raise smtplib.SMTPConnectError(421, "connexion refusée")


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


def test_envoyer_alerte_envoie_un_message_smtp_complet(monkeypatch):
    """Vérifie le message dans son ensemble, pas seulement le sujet -- From/To comptent
    aussi : une inversion ou une faute de frappe sur ces constantes passerait inaperçue sinon."""
    monkeypatch.setattr("datacore.alerting.webhook.smtplib.SMTP", FakeSMTP)

    envoyer_alerte("sujet de test", "corps de test", hote_smtp="fake-host", port_smtp=1025)

    assert len(FakeSMTP.messages_envoyes) == 1
    message = FakeSMTP.messages_envoyes[0]
    assert message["Subject"] == "sujet de test"
    assert message["From"] == EXPEDITEUR
    assert message["To"] == DESTINATAIRE
    assert message.get_content().strip() == "corps de test"


def test_envoyer_alerte_echec_smtp_leve_une_exception_smtp(monkeypatch):
    """`envoyer_alerte()` elle-même ne rattrape rien -- c'est la route qui décide quoi
    faire d'un échec SMTP (voir test_route_webhook_alertes_echec_smtp_renvoie_502)."""
    monkeypatch.setattr("datacore.alerting.webhook.smtplib.SMTP", FakeSMTPEnPanne)

    with pytest.raises(smtplib.SMTPException):
        envoyer_alerte("sujet", "corps", hote_smtp="fake-host", port_smtp=1025)


def test_route_webhook_alertes_sans_secret_refuse_401(client):
    reponse = client.post(
        "/webhook/alertes",
        json={"status": "firing", "alerts": []},
    )
    assert reponse.status_code == 401
    assert FakeSMTP.messages_envoyes == []


def test_route_webhook_alertes_mauvais_secret_refuse_401(client):
    reponse = client.post(
        "/webhook/alertes",
        json={"status": "firing", "alerts": []},
        headers={"X-Webhook-Secret": "mauvaise-valeur"},
    )
    assert reponse.status_code == 401


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
        headers=EN_TETES_VALIDES,
    )

    assert reponse.status_code == 200
    assert len(FakeSMTP.messages_envoyes) == 1
    assert "TestAlerte" in FakeSMTP.messages_envoyes[0]["Subject"]


def test_route_webhook_alertes_payload_liste_refuse_400(client):
    """Un payload JSON valide mais de la mauvaise forme (une liste, pas un objet) --
    `silent=True` ne rattrape que le JSON invalide, pas le JSON valide-mais-mauvaise-forme :
    sans contrôle explicite, `[1, 2, 3].get(...)` lèverait une AttributeError non gérée."""
    reponse = client.post(
        "/webhook/alertes",
        data="[1, 2, 3]",
        content_type="application/json",
        headers=EN_TETES_VALIDES,
    )
    assert reponse.status_code == 400
    assert FakeSMTP.messages_envoyes == []


def test_route_webhook_alertes_json_malforme_refuse_400(client):
    reponse = client.post(
        "/webhook/alertes",
        data="ceci nest pas du json",
        content_type="application/json",
        headers=EN_TETES_VALIDES,
    )
    assert reponse.status_code == 400


def test_route_webhook_alertes_echec_smtp_renvoie_502(client, monkeypatch):
    """Un échec SMTP (ex. MailHog injoignable) doit renvoyer une erreur explicite (502),
    pas un 500 générique -- pour que Grafana voie un échec de notification exploitable."""
    monkeypatch.setattr("datacore.alerting.webhook.smtplib.SMTP", FakeSMTPEnPanne)

    reponse = client.post(
        "/webhook/alertes",
        json={"status": "firing", "alerts": []},
        headers=EN_TETES_VALIDES,
    )

    assert reponse.status_code == 502
    assert "erreur" in reponse.get_json()


def test_route_health_sans_authentification(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.get_json()["status"] == "ok"
