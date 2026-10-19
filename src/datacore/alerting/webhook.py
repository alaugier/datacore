"""Relais d'alerte Grafana → e-mail (C20bis).

Le référentiel de compétences exige que *« le monitorage génère une
alerte lors d'une rupture de service »* (C20, voir
`docs/reference/Referentiel_Activites_Competences_Evaluation_DE.pdf`
page 24). Grafana détecte la rupture (règle d'alerte sur
`monitoring.sante_infrastructure`/`monitoring.catalogue_lake`, voir
`infra/grafana/provisioning/alerting/`) et appelle ce service en
webhook ; ce module relaie l'alerte en e-mail réel via `smtplib`, vers
un capteur SMTP local (MailHog, `infra/docker/docker-compose.yml`) —
jamais un vrai fournisseur externe (voir
`docs/architecture/gestion_operationnelle_omega_bi.md` pour la
justification de ce choix plutôt qu'un vrai compte Gmail).

Service Flask séparé d'`api-mock` : `api-mock` simule les sources de
données externes d'Omega Logistics (FluxPro/TransFlow), ce webhook est
un outil interne d'observabilité, sans rapport thématique avec les
sources métier.
"""
import smtplib
from email.message import EmailMessage

from flask import Flask, abort, jsonify, request

from datacore.config import ALERTING_WEBHOOK_SECRET, SMTP_HOST, SMTP_PORT

app = Flask(__name__)

EXPEDITEUR = "alerting@datacore.local"
DESTINATAIRE = "data-engineer@datacore.local"


def require_webhook_secret() -> None:
    """Interrompt la requête avec un 401 si l'en-tête `X-Webhook-Secret` est absent ou invalide.

    Le port du service est exposé sur l'hôte (`docker-compose.yml`) --
    sans ce contrôle, n'importe quel process local pourrait déclencher
    un envoi d'e-mail. Grafana envoie ce secret via l'en-tête
    personnalisé configuré sur le point de contact (voir
    `infra/grafana/provisioning/alerting/lake_monitoring.yaml`).
    """
    secret = request.headers.get("X-Webhook-Secret")
    if secret != ALERTING_WEBHOOK_SECRET:
        abort(401, description="Secret manquant ou invalide. En-tête attendu : X-Webhook-Secret")


@app.errorhandler(401)
def unauthorized(e):
    """Sérialise les erreurs 401 (secret manquant/invalide) en JSON."""
    return jsonify({"erreur": "unauthorized", "message": str(e.description)}), 401


def envoyer_alerte(
    sujet: str, corps: str, hote_smtp: str = SMTP_HOST, port_smtp: int = SMTP_PORT
) -> None:
    """Envoie un e-mail d'alerte réel via SMTP (smtplib), vers un capteur local.

    Args:
        sujet: sujet de l'e-mail.
        corps: corps du message (texte brut).
        hote_smtp: hôte du serveur SMTP (MailHog en local/CI).
        port_smtp: port du serveur SMTP.
    """
    message = EmailMessage()
    message["Subject"] = sujet
    message["From"] = EXPEDITEUR
    message["To"] = DESTINATAIRE
    message.set_content(corps)

    with smtplib.SMTP(hote_smtp, port_smtp) as smtp:
        smtp.send_message(message)


def _resumer_payload(payload: dict) -> tuple[str, str]:
    """Extrait un sujet/corps lisibles du payload webhook de Grafana.

    Le format exact varie selon la version de Grafana ; on ne dépend
    que des clés les plus stables (`status`, `alerts[].labels.alertname`,
    `alerts[].annotations.summary`) et on retombe sur le payload brut si
    la structure attendue est absente, plutôt que de lever une erreur.

    Args:
        payload: corps JSON reçu du webhook Grafana.

    Returns:
        `(sujet, corps)`.
    """
    statut = payload.get("status", "inconnu")
    alertes = payload.get("alerts", [])
    if not alertes:
        return f"[DATA CORE] Alerte Grafana ({statut})", str(payload)

    noms = [a.get("labels", {}).get("alertname", "?") for a in alertes]
    resumes = [a.get("annotations", {}).get("summary", "") for a in alertes]
    sujet = f"[DATA CORE] Alerte Grafana ({statut}) : {', '.join(noms)}"
    corps = "\n".join(f"- {nom} : {resume}" for nom, resume in zip(noms, resumes, strict=True))
    return sujet, corps


@app.get("/health")
def health():
    """Vérifie la disponibilité du service (sans authentification)."""
    return jsonify({"status": "ok", "service": "alerting-webhook"})


@app.post("/webhook/alertes")
def recevoir_alerte():
    """Reçoit le webhook d'alerte de Grafana et relaie un e-mail réel via SMTP.

    Returns:
        200 si l'e-mail a été relayé. 400 si le payload reçu n'est pas
        un objet JSON (ex. une liste ou une chaîne -- un payload JSON
        valide mais de la mauvaise forme n'est pas intercepté par
        `silent=True`, qui ne couvre que le JSON invalide). 502 si
        l'envoi SMTP échoue (ex. MailHog injoignable) -- pour que
        Grafana voie un échec de notification explicite plutôt qu'un
        500 générique.
    """
    require_webhook_secret()

    payload = request.get_json(force=True, silent=True)
    if not isinstance(payload, dict):
        return jsonify({"erreur": "payload JSON invalide (un objet est attendu)"}), 400

    sujet, corps = _resumer_payload(payload)
    try:
        envoyer_alerte(sujet, corps)
    except (OSError, smtplib.SMTPException) as erreur:
        return jsonify({"erreur": f"échec de l'envoi SMTP : {erreur}"}), 502

    return jsonify({"statut": "relayé"}), 200


if __name__ == "__main__":
    from datacore.config import ALERTING_WEBHOOK_PORT

    app.run(host="0.0.0.0", port=int(ALERTING_WEBHOOK_PORT))
