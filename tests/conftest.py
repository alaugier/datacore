"""Fixtures pytest partagees pour les tests unitaires et d'integration.

Charge dynamiquement le module `api-mock/app.py` (nom de dossier avec
tiret, donc non importable via un `import` classique) afin de le tester
sans dependre du serveur Flask reellement lance.
"""
import importlib.util
import pathlib
import sys
import threading

import pytest
from werkzeug.serving import make_server

API_MOCK_DIR = pathlib.Path(__file__).resolve().parents[1] / "api-mock"
sys.path.insert(0, str(API_MOCK_DIR))


def _load_api_mock_app():
    """Charge `api-mock/app.py` comme module Python autonome.

    Returns:
        module: le module `app` de l'API mock TransFlow, avec son objet
            Flask (`app.app`) et ses fonctions utilitaires (`paginate`, ...).
    """
    spec = importlib.util.spec_from_file_location("api_mock_app", API_MOCK_DIR / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def api_mock_module():
    """Module `app.py` de l'API mock, charge une seule fois par session de tests."""
    return _load_api_mock_app()


@pytest.fixture()
def api_client(api_mock_module):
    """Client de test Flask pour appeler l'API mock sans serveur reseau reel."""
    api_mock_module.app.testing = True
    return api_mock_module.app.test_client()


@pytest.fixture()
def api_key(api_mock_module):
    """Cle API valide attendue par l'API mock (en-tete X-API-Key)."""
    return api_mock_module.API_KEY


@pytest.fixture(scope="session")
def live_api_mock(api_mock_module):
    """URL de base d'un serveur Flask reel (l'API mock), lance en arriere-plan.

    Contrairement a `api_client` (client de test Flask, pas de vrai
    reseau), cette fixture permet de tester des clients HTTP (module
    `requests`, utilises par `datacore.ingestion.transflow` et
    `datacore.ingestion.portail_scraping`) sans dependre d'un processus
    `python3 app.py` deja lance manuellement.

    Yields:
        str: l'URL de base du serveur (ex. "http://127.0.0.1:54321").
    """
    server = make_server("127.0.0.1", 0, api_mock_module.app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=5)
