"""Tests d'intégration des routes de l'Omega Data API (C12).

Teste l'authentification JWT (émission du jeton via `/auth/token`,
vérification sur les routes protégées), l'autorisation par rôle et la
forme des réponses via le `TestClient` FastAPI. La couche d'accès aux
données (`datacore.api.repository`) est remplacée par des doubles (via
`monkeypatch`) : ces tests valident le comportement des routes (auth,
scoping, codes HTTP), pas la correction du SQL — couverte par
`tests/unit/test_api_repository.py` et un test de bout en bout contre
une vraie base.
"""
import pytest
from fastapi.testclient import TestClient

from datacore.api import main as api_main
from datacore.api.db import get_db
from datacore.api.main import app

ENGINEER_KEY = "omega-data-engineer-2026"
ANALYST_KEY = "omega-data-analyst-2026"
NORDDRIVE_KEY = "omega-norddrive-2026"
FRESHMARKET_KEY = "omega-freshmarket-2026"


@pytest.fixture()
def client():
    """TestClient avec la dépendance DB neutralisée (repository mocké par test)."""
    app.dependency_overrides[get_db] = lambda: "fake-connection"
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, api_key: str) -> dict[str, str]:
    """Échange une clé API contre un jeton JWT (POST /auth/token) et renvoie
    l'en-tête Authorization prêt à l'emploi -- reproduit ce que ferait un
    vrai appelant depuis le 19/11/2026 (plus de clé envoyée directement).
    """
    resp = client.post("/auth/token", data={"username": api_key, "password": ""})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_does_not_require_auth(client):
    """La route de santé est accessible sans authentification."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_token_issued_for_valid_api_key(client):
    """Une clé API connue est échangée contre un jeton JWT exploitable (bearer)."""
    resp = client.post("/auth/token", data={"username": ENGINEER_KEY, "password": ""})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_token_refused_for_unknown_api_key(client):
    """Une clé API inconnue est refusée (401) dès l'émission du jeton."""
    resp = client.post("/auth/token", data={"username": "cle-invalide", "password": ""})
    assert resp.status_code == 401


def test_missing_token_is_rejected(client):
    """Toute route de données sans jeton (en-tête Authorization) est rejetée (401)."""
    resp = client.get("/commandes-clients")
    assert resp.status_code == 401


def test_invalid_token_is_rejected(client):
    """Un jeton mal formé/invalide est rejeté (401)."""
    resp = client.get("/commandes-clients", headers={"Authorization": "Bearer pas-un-vrai-jwt"})
    assert resp.status_code == 401


def test_data_engineer_sees_any_client(client, monkeypatch):
    """Un rôle interne peut filtrer sur n'importe quel client, sans restriction."""
    captured = {}

    def fake_list(conn, client=None, limit=50, offset=0):
        captured["client"] = client
        return []

    monkeypatch.setattr(api_main.repository, "list_commandes_clients", fake_list)

    resp = client.get(
        "/commandes-clients?client=FreshMarket", headers=auth_headers(client, ENGINEER_KEY)
    )

    assert resp.status_code == 200
    assert captured["client"] == "FreshMarket"


def test_client_referent_scope_overrides_requested_client(client, monkeypatch):
    """Un référent NordDrive demandant FreshMarket est ramené à son propre périmètre."""
    captured = {}

    def fake_list(conn, client=None, limit=50, offset=0):
        captured["client"] = client
        return []

    monkeypatch.setattr(api_main.repository, "list_commandes_clients", fake_list)

    resp = client.get(
        "/commandes-clients?client=FreshMarket", headers=auth_headers(client, NORDDRIVE_KEY)
    )

    assert resp.status_code == 200
    assert captured["client"] == "NordDrive"


def test_client_referent_cannot_access_livraisons(client):
    """Les référents clients n'ont pas accès aux données de transport."""
    resp = client.get("/livraisons", headers=auth_headers(client, NORDDRIVE_KEY))
    assert resp.status_code == 403


def test_data_analyst_can_access_livraisons(client, monkeypatch):
    """Un rôle interne (Data Analyst) accède aux livraisons."""
    monkeypatch.setattr(api_main.repository, "list_livraisons", lambda *a, **k: [])

    resp = client.get("/livraisons", headers=auth_headers(client, ANALYST_KEY))

    assert resp.status_code == 200


def test_livraisons_rejects_invalid_statut_value(client, monkeypatch):
    """Un statut hors {Livree, En cours} est rejeté (422), pas silencieusement filtré à vide."""
    called = False

    def fake_list(*args, **kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(api_main.repository, "list_livraisons", fake_list)

    resp = client.get(
        "/livraisons?statut=en_retard", headers=auth_headers(client, ANALYST_KEY)
    )

    assert resp.status_code == 422
    assert called is False  # rejeté avant meme d'atteindre la couche de donnees


def test_livraisons_accepts_valid_statut_values(client, monkeypatch):
    """Les deux valeurs valides sont acceptées."""
    monkeypatch.setattr(api_main.repository, "list_livraisons", lambda *a, **k: [])

    headers = auth_headers(client, ANALYST_KEY)
    for statut in ("Livree", "En cours"):
        resp = client.get(f"/livraisons?statut={statut}", headers=headers)
        assert resp.status_code == 200


def test_client_referent_cannot_see_another_clients_commande_lines(client, monkeypatch):
    """Un référent ne peut pas consulter les lignes d'une commande d'un autre client."""
    monkeypatch.setattr(
        api_main.repository,
        "get_commande_client",
        lambda conn, cid: {
            "id": cid,
            "client": "FreshMarket",
            "commande_id": "FM-1",
            "date_commande": "2026-01-01",
            "entrepot": "OMG-LYO",
        },
    )

    resp = client.get(
        "/commandes-clients/1/lignes", headers=auth_headers(client, NORDDRIVE_KEY)
    )

    assert resp.status_code == 403


def test_client_referent_can_see_own_commande_lines(client, monkeypatch):
    """Un référent peut consulter les lignes d'une commande de son propre client."""
    monkeypatch.setattr(
        api_main.repository,
        "get_commande_client",
        lambda conn, cid: {
            "id": cid,
            "client": "NordDrive",
            "commande_id": "ND-1",
            "date_commande": "2026-01-01",
            "entrepot": "OMG-LYO",
        },
    )
    monkeypatch.setattr(api_main.repository, "list_lignes_commande_client", lambda conn, cid: [])

    resp = client.get(
        "/commandes-clients/1/lignes", headers=auth_headers(client, NORDDRIVE_KEY)
    )

    assert resp.status_code == 200


def test_unknown_commande_returns_404(client, monkeypatch):
    """Une commande inexistante renvoie 404, pas une erreur serveur."""
    monkeypatch.setattr(api_main.repository, "get_commande_client", lambda conn, cid: None)

    resp = client.get(
        "/commandes-clients/999/lignes", headers=auth_headers(client, ENGINEER_KEY)
    )

    assert resp.status_code == 404


def test_taux_service_scoped_for_client_referent(client, monkeypatch):
    """Le KPI taux de service est restreint au client du référent qui le consulte."""
    captured = {}

    def fake_taux(conn, client=None):
        captured["client"] = client
        return []

    monkeypatch.setattr(api_main.repository, "taux_service_par_client", fake_taux)

    resp = client.get("/kpis/taux-service", headers=auth_headers(client, FRESHMARKET_KEY))

    assert resp.status_code == 200
    assert captured["client"] == "FreshMarket"
