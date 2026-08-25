"""Tests unitaires de la fonction de pagination de l'API mock TransFlow.

Ne necessitent ni serveur Flask ni requete HTTP : `paginate()` est une
fonction pure, testee directement avec des objets requete factices.
"""


class FakeRequest:
    """Substitut minimal de `flask.request`, pour tester `paginate()` isolement.

    Args:
        args: dict simulant `request.args` (parametres de query string).
    """

    def __init__(self, args):
        self.args = args


def test_paginate_default_page_and_per_page(api_mock_module):
    """Sans parametre, page=1 et per_page=50 (valeurs par defaut de l'API)."""
    items = list(range(120))
    result = api_mock_module.paginate(items, FakeRequest({}))
    assert result["page"] == 1
    assert result["per_page"] == 50
    assert result["total"] == 120
    assert result["total_pages"] == 3
    assert result["results"] == items[:50]


def test_paginate_caps_per_page_at_200(api_mock_module):
    """Un per_page demande superieur a 200 est plafonne a 200."""
    items = list(range(300))
    result = api_mock_module.paginate(items, FakeRequest({"per_page": "500"}))
    assert result["per_page"] == 200
    assert len(result["results"]) == 200


def test_paginate_invalid_params_fall_back_to_defaults(api_mock_module):
    """Des parametres non numeriques ne font pas planter la pagination."""
    items = list(range(10))
    result = api_mock_module.paginate(items, FakeRequest({"page": "abc", "per_page": "xyz"}))
    assert result["page"] == 1
    assert result["per_page"] == 50


def test_paginate_out_of_range_page_returns_empty_results(api_mock_module):
    """Une page au-dela du nombre d'elements renvoie une liste vide, pas une erreur."""
    items = list(range(5))
    result = api_mock_module.paginate(items, FakeRequest({"page": "10"}))
    assert result["total"] == 5
    assert result["results"] == []


def test_paginate_second_page_offset(api_mock_module):
    """La page 2 commence bien apres le decalage `per_page` de la page 1."""
    items = list(range(25))
    result = api_mock_module.paginate(items, FakeRequest({"page": "2", "per_page": "10"}))
    assert result["results"] == items[10:20]
