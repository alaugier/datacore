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

from flask import Flask, jsonify, request

from datacore.config import SMTP_HOST, SMTP_PORT

app = Flask(__name__)

EXPEDITEUR = "alerting@datacore.local"
DESTINATAIRE = "data-engineer@datacore.local"


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
    """Reçoit le webhook d'alerte de Grafana et relaie un e-mail réel via SMTP."""
    payload = request.get_json(force=True, silent=True) or {}
    sujet, corps = _resumer_payload(payload)
    envoyer_alerte(sujet, corps)
    return jsonify({"statut": "relayé"}), 200


if __name__ == "__main__":
    from datacore.config import ALERTING_WEBHOOK_PORT

    app.run(host="0.0.0.0", port=int(ALERTING_WEBHOOK_PORT))
