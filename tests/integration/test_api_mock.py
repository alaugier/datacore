"""Tests d'integration de l'API mock TransFlow (couverture C8/C12).

Exercent le serveur Flask via son client de test (`api_client`, defini
dans `tests/conftest.py`) : authentification, pagination, filtres et
portail transporteur a scraper.
"""


def test_health_does_not_require_auth(api_client):
    """La route de sante est accessible sans cle API."""
    resp = api_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_transporteurs_requires_api_key(api_client):
    """Toute route /api/* sans en-tete X-API-Key est rejetee (401)."""
    resp = api_client.get("/api/transporteurs")
    assert resp.status_code == 401


def test_transporteurs_with_valid_key(api_client, api_key):
    """Avec une cle API valide, la liste des 3 transporteurs fictifs est renvoyee."""
    resp = api_client.get("/api/transporteurs", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 3


def test_tournees_pagination(api_client, api_key):
    """Le parametre per_page limite bien le nombre de resultats renvoyes."""
    resp = api_client.get(
        "/api/tournees?per_page=10&page=1", headers={"X-API-Key": api_key}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["per_page"] == 10
    assert len(data["results"]) == 10


def test_tournee_not_found(api_client, api_key):
    """Une tournee dont l'id n'existe pas renvoie 404, pas une erreur serveur."""
    resp = api_client.get("/api/tournees/999999", headers={"X-API-Key": api_key})
    assert resp.status_code == 404


def test_livraisons_filter_by_statut(api_client, api_key):
    """Le filtre `statut` ne renvoie que les livraisons du statut demande."""
    resp = api_client.get(
        "/api/livraisons?statut=Livree&per_page=200", headers={"X-API-Key": api_key}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["results"]
    assert all(liv["statut"] == "Livree" for liv in data["results"])


def test_portail_transporteur_colis_lists_links(api_client):
    """La page d'index du portail transporteur (a scraper) repond en HTML."""
    resp = api_client.get("/portail-transporteur/colis")
    assert resp.status_code == 200
    assert b"Portail de suivi transporteur" in resp.data


def test_portail_transporteur_colis_detail_not_found(api_client):
    """Un tracking number inconnu sur le portail transporteur renvoie 404."""
    resp = api_client.get("/portail-transporteur/colis/UNKNOWN-TRACKING")
    assert resp.status_code == 404
