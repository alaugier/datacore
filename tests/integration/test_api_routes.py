"""Tests d'intégration des routes de l'Omega Data API (C12).

Teste l'authentification, l'autorisation par rôle et la forme des
réponses via le `TestClient` FastAPI. La couche d'accès aux données
(`datacore.api.repository`) est remplacée par des doubles (via
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


def test_health_does_not_require_auth(client):
    """La route de santé est accessible sans clé API."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_missing_api_key_is_rejected(client):
    """Toute route de données sans en-tête X-API-Key est rejetée (401)."""
    resp = client.get("/commandes-clients")
    assert resp.status_code == 401


def test_invalid_api_key_is_rejected(client):
    """Une clé API inconnue est rejetée (401)."""
    resp = client.get("/commandes-clients", headers={"X-API-Key": "cle-invalide"})
    assert resp.status_code == 401


def test_data_engineer_sees_any_client(client, monkeypatch):
    """Un rôle interne peut filtrer sur n'importe quel client, sans restriction."""
    captured = {}

    def fake_list(conn, client=None, limit=50, offset=0):
        captured["client"] = client
        return []

    monkeypatch.setattr(api_main.repository, "list_commandes_clients", fake_list)

    resp = client.get(
        "/commandes-clients?client=FreshMarket", headers={"X-API-Key": ENGINEER_KEY}
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
        "/commandes-clients?client=FreshMarket", headers={"X-API-Key": NORDDRIVE_KEY}
    )

    assert resp.status_code == 200
    assert captured["client"] == "NordDrive"


def test_client_referent_cannot_access_livraisons(client):
    """Les référents clients n'ont pas accès aux données de transport."""
    resp = client.get("/livraisons", headers={"X-API-Key": NORDDRIVE_KEY})
    assert resp.status_code == 403


def test_data_analyst_can_access_livraisons(client, monkeypatch):
    """Un rôle interne (Data Analyst) accède aux livraisons."""
    monkeypatch.setattr(api_main.repository, "list_livraisons", lambda *a, **k: [])

    resp = client.get("/livraisons", headers={"X-API-Key": ANALYST_KEY})

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

    resp = client.get("/commandes-clients/1/lignes", headers={"X-API-Key": NORDDRIVE_KEY})

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

    resp = client.get("/commandes-clients/1/lignes", headers={"X-API-Key": NORDDRIVE_KEY})

    assert resp.status_code == 200


def test_unknown_commande_returns_404(client, monkeypatch):
    """Une commande inexistante renvoie 404, pas une erreur serveur."""
    monkeypatch.setattr(api_main.repository, "get_commande_client", lambda conn, cid: None)

    resp = client.get("/commandes-clients/999/lignes", headers={"X-API-Key": ENGINEER_KEY})

    assert resp.status_code == 404


def test_taux_service_scoped_for_client_referent(client, monkeypatch):
    """Le KPI taux de service est restreint au client du référent qui le consulte."""
    captured = {}

    def fake_taux(conn, client=None):
        captured["client"] = client
        return []

    monkeypatch.setattr(api_main.repository, "taux_service_par_client", fake_taux)

    resp = client.get("/kpis/taux-service", headers={"X-API-Key": FRESHMARKET_KEY})

    assert resp.status_code == 200
    assert captured["client"] == "FreshMarket"
