"""Fixtures pytest partagees pour les tests unitaires et d'integration.

Charge dynamiquement le module `api-mock/app.py` (nom de dossier avec
tiret, donc non importable via un `import` classique) afin de le tester
sans dependre du serveur Flask reellement lance.
"""
import importlib.util
import pathlib
import sys

import pytest

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
