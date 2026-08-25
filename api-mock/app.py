#!/usr/bin/env python3
"""
API mock "TransFlow" + portail transporteur (scraping) + flux capteurs (streaming)
--------------------------------------------------------------------------------
Sert de source de donnees pour le bloc de competences 2 (collecte, C8-C12) et
le bloc 4 (data lake, C18-C21) du projet fictif DATA CORE.

Lancement :
    pip install flask
    python3 app.py
    -> API disponible sur http://127.0.0.1:5050

Authentification : toutes les routes /api/* necessitent l'en-tete
    X-API-Key: datacore-training-2026
(clef fictive a usage pedagogique, volontairement simple)

Endpoints :
    GET  /api/health
    GET  /api/transporteurs
    GET  /api/tournees?date=YYYY-MM-DD&transporteur_id=1&page=1&per_page=50
    GET  /api/tournees/<id>
    GET  /api/tournees/<id>/livraisons
    GET  /api/livraisons?statut=Livree&page=1&per_page=50
    GET  /api/livraisons/<id>
    GET  /api/stream/capteurs   (Server-Sent Events -- flux temps reel simule)

    GET  /portail-transporteur/colis                (page HTML a parcourir)
    GET  /portail-transporteur/colis/<tracking_nb>   (page HTML a scraper)
"""
import json
import os
import random
import time
from datetime import datetime

from flask import Flask, Response, abort, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures")
API_KEY = "datacore-training-2026"

app = Flask(__name__)


def load_json(name):
    """Charge un fichier JSON de fixtures.

    Args:
        name: nom du fichier a charger, relatif a `api-mock/fixtures/`
            (ex. "transporteurs.json").

    Returns:
        Le contenu desserialise du fichier JSON.
    """
    with open(os.path.join(FIXTURES_DIR, name), encoding="utf-8") as f:
        return json.load(f)


TRANSPORTEURS = load_json("transporteurs.json")
TOURNEES = load_json("tournees.json")
LIVRAISONS = load_json("livraisons.json")
LIVRAISONS_BY_TRACKING = {liv["tracking_number"]: liv for liv in LIVRAISONS}


def require_api_key():
    """Interrompt la requete avec un 401 si l'en-tete X-API-Key est absent ou invalide."""
    key = request.headers.get("X-API-Key")
    if key != API_KEY:
        abort(401, description="Cle API manquante ou invalide. En-tete attendu : X-API-Key")


def paginate(items, req):
    """Pagine une liste selon les parametres `page`/`per_page` de la requete.

    Args:
        items: liste complete des elements a paginer.
        req: objet requete exposant `.args.get(...)` (typiquement
            `flask.request`, ou un objet compatible dans les tests).

    Returns:
        dict avec les cles `page`, `per_page`, `total`, `total_pages`
        et `results` (la tranche d'elements de la page demandee).
        En cas de parametres invalides, retombe sur page=1, per_page=50.
        `per_page` est plafonne a 200.
    """
    try:
        page = max(1, int(req.args.get("page", 1)))
        per_page = min(200, max(1, int(req.args.get("per_page", 50))))
    except ValueError:
        page = 1
        per_page = 50
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "page": page,
        "per_page": per_page,
        "total": len(items),
        "total_pages": max(1, (len(items) + per_page - 1) // per_page),
        "results": items[start:end],
    }


@app.errorhandler(401)
def unauthorized(e):
    """Serialise les erreurs 401 (cle API manquante/invalide) en JSON."""
    return jsonify({"error": "unauthorized", "message": str(e.description)}), 401


@app.errorhandler(404)
def not_found(e):
    """Serialise les erreurs 404 (ressource introuvable) en JSON."""
    return jsonify({"error": "not_found", "message": str(e.description)}), 404


@app.get("/api/health")
def health():
    """Verifie la disponibilite du service (sans authentification)."""
    return jsonify({
        "status": "ok",
        "service": "TransFlow API (mock pedagogique)",
        "time": datetime.utcnow().isoformat(),
    })


@app.get("/api/transporteurs")
def get_transporteurs():
    """Liste l'ensemble des transporteurs fictifs."""
    require_api_key()
    return jsonify(TRANSPORTEURS)


@app.get("/api/tournees")
def get_tournees():
    """Liste les tournees, filtrables par date et transporteur, paginees."""
    require_api_key()
    items = TOURNEES
    date = request.args.get("date")
    transporteur_id = request.args.get("transporteur_id")
    if date:
        items = [t for t in items if t["date"] == date]
    if transporteur_id:
        items = [t for t in items if str(t["transporteur_id"]) == str(transporteur_id)]
    return jsonify(paginate(items, request))


@app.get("/api/tournees/<int:tournee_id>")
def get_tournee(tournee_id):
    """Recupere le detail d'une tournee par son id (404 si absente).

    Args:
        tournee_id: identifiant de la tournee, extrait de l'URL.
    """
    require_api_key()
    t = next((x for x in TOURNEES if x["id"] == tournee_id), None)
    if not t:
        abort(404, description=f"Tournee {tournee_id} introuvable")
    return jsonify(t)


@app.get("/api/tournees/<int:tournee_id>/livraisons")
def get_tournee_livraisons(tournee_id):
    """Liste les livraisons rattachees a une tournee (404 si aucune).

    Args:
        tournee_id: identifiant de la tournee, extrait de l'URL.
    """
    require_api_key()
    items = [liv for liv in LIVRAISONS if liv["tournee_id"] == tournee_id]
    if not items:
        abort(404, description=f"Aucune livraison pour la tournee {tournee_id}")
    return jsonify(items)


@app.get("/api/livraisons")
def get_livraisons():
    """Liste les livraisons, filtrables par statut, paginees."""
    require_api_key()
    items = LIVRAISONS
    statut = request.args.get("statut")
    if statut:
        items = [liv for liv in items if liv["statut"].lower() == statut.lower()]
    return jsonify(paginate(items, request))


@app.get("/api/livraisons/<int:livraison_id>")
def get_livraison(livraison_id):
    """Recupere le detail d'une livraison par son id (404 si absente).

    Args:
        livraison_id: identifiant de la livraison, extrait de l'URL.
    """
    require_api_key()
    liv = next((x for x in LIVRAISONS if x["id"] == livraison_id), None)
    if not liv:
        abort(404, description=f"Livraison {livraison_id} introuvable")
    return jsonify(liv)


# ---------------------------------------------------------------------
# Flux capteurs temps reel simule (Server-Sent Events) -- generique,
# a consommer avec l'outil de son choix (aucun broker impose).
# ---------------------------------------------------------------------
ZONES_FROIDES = [
    ("OMG-LYO", "Zone froide A"),
    ("OMG-LIL", "Zone froide B"),
    ("OMG-MAR", "Zone froide A"),
]


@app.get("/api/stream/capteurs")
def stream_capteurs():
    """Diffuse un flux continu de mesures capteurs simulees (Server-Sent Events).

    Anticipe le bloc 4 (data lake OMEGA LAKE, C18-C20) : temperature,
    geolocalisation et identifiant vehicule, un evenement toutes les 2s.
    """
    require_api_key()

    def event_stream():
        """Generateur infini d'evenements SSE au format `data: <json>\\n\\n`."""
        while True:
            entrepot, zone = random.choice(ZONES_FROIDES)
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "entrepot": entrepot,
                "zone": zone,
                "temperature_c": round(random.gauss(3.0, 1.0), 2),
                "vehicule_id": f"VH-{random.randint(1,15):03d}",
                "lat": round(45.0 + random.uniform(-3, 3), 5),
                "lon": round(3.0 + random.uniform(-3, 3), 5),
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            time.sleep(2)

    return Response(event_stream(), mimetype="text/event-stream")


# ---------------------------------------------------------------------
# Portail transporteur -- page HTML a scraper (source "page web / scraping")
# ---------------------------------------------------------------------
PORTAL_STYLE = """
<style>
body{font-family:Arial,sans-serif;max-width:720px;margin:40px auto;color:#222}
h1{color:#1F3864} table{border-collapse:collapse;width:100%}
td,th{border:1px solid #ccc;padding:6px 10px;text-align:left}
.badge{padding:2px 8px;border-radius:10px;font-size:12px;color:#fff}
.livree{background:#2e7d32}.encours{background:#e08e00}
</style>
"""


@app.get("/portail-transporteur/colis")
def portail_index():
    """Sert la page HTML listant un echantillon de colis (source a scraper)."""
    sample = random.sample(LIVRAISONS, min(40, len(LIVRAISONS)))
    rows = "".join(
        f'<li><a href="/portail-transporteur/colis/{liv["tracking_number"]}">'
        f'{liv["tracking_number"]}</a> &mdash; {liv["statut"]}</li>'
        for liv in sample
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8">
    <title>Portail de suivi transporteur</title>{PORTAL_STYLE}</head>
    <body><h1>Portail de suivi transporteur (fictif)</h1>
    <p>Page d'exemple a parcourir/scraper. Liste non exhaustive de colis :</p>
    <ul>{rows}</ul></body></html>"""
    return Response(html, mimetype="text/html")


@app.get("/portail-transporteur/colis/<tracking_number>")
def portail_colis(tracking_number):
    """Sert la fiche HTML de suivi d'un colis (source a scraper), 404 si inconnu.

    Args:
        tracking_number: numero de suivi du colis, extrait de l'URL.
    """
    liv = LIVRAISONS_BY_TRACKING.get(tracking_number)
    if not liv:
        abort(404, description=f"Colis {tracking_number} introuvable")
    badge_class = "livree" if liv["statut"] == "Livree" else "encours"
    html = f"""<!doctype html><html><head><meta charset="utf-8">
    <title>Suivi colis {tracking_number}</title>{PORTAL_STYLE}</head>
    <body>
    <h1>Suivi du colis {tracking_number}</h1>
    <table>
      <tr><th>Statut</th><td><span class="badge {badge_class}">{liv['statut']}</span></td></tr>
      <tr><th>Adresse de livraison</th><td>{liv['adresse_livraison']}</td></tr>
      <tr><th>Heure estimee</th><td>{liv['heure_estimee']}</td></tr>
      <tr><th>Heure reelle</th><td>{liv['heure_reelle'] or '-'}</td></tr>
      <tr><th>Tournee</th><td>{liv['tournee_id']}</td></tr>
    </table>
    <p><a href="/portail-transporteur/colis">&larr; retour a la liste</a></p>
    </body></html>"""
    return Response(html, mimetype="text/html")


@app.get("/")
def index():
    """Page d'accueil : recapitule les endpoints disponibles."""
    return jsonify({
        "service": "DATA CORE - API mock pedagogique (TransFlow + portail transporteur)",
        "documentation": "voir README.md a la racine du projet",
        "endpoints": [
            "/api/health", "/api/transporteurs", "/api/tournees", "/api/tournees/<id>",
            "/api/tournees/<id>/livraisons", "/api/livraisons", "/api/livraisons/<id>",
            "/api/stream/capteurs", "/portail-transporteur/colis",
            "/portail-transporteur/colis/<tracking_number>",
        ],
    })


if __name__ == "__main__":
    host = os.environ.get("API_MOCK_HOST", "127.0.0.1")
    app.run(host=host, port=5050, debug=False, threaded=True)
