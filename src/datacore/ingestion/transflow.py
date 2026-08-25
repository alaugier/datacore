"""Extraction des données TransFlow (tournées, livraisons, transporteurs) via l'API REST (C8).

Couvre la source « service web » attendue par le référentiel (voir
`docs/architecture/topographie_donnees.md` section 2). L'API mock pagine
ses réponses (`page`, `per_page`) : ce module boucle automatiquement sur
toutes les pages pour renvoyer la collection complète.
"""
from typing import Any

import requests

from datacore.ingestion.config import TRANSFLOW_API_KEY, TRANSFLOW_API_URL

MAX_PER_PAGE = 200


def _headers() -> dict[str, str]:
    """En-têtes HTTP requis par les routes /api/* de TransFlow."""
    return {"X-API-Key": TRANSFLOW_API_KEY}


def _get_json(path: str, params: dict[str, Any] | None, base_url: str) -> Any:
    """Effectue un GET authentifié sur l'API TransFlow et renvoie le JSON.

    Args:
        path: chemin de la route, ex. "/api/transporteurs".
        params: paramètres de requête optionnels (filtres, pagination).
        base_url: racine de l'API (surclassable pour les tests).

    Returns:
        Le corps de la réponse désérialisé.
    """
    resp = requests.get(f"{base_url}{path}", headers=_headers(), params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_transporteurs(base_url: str = TRANSFLOW_API_URL) -> list[dict[str, Any]]:
    """Récupère la liste complète des transporteurs.

    Args:
        base_url: racine de l'API TransFlow.

    Returns:
        La liste des transporteurs.
    """
    return _get_json("/api/transporteurs", None, base_url)


def _fetch_paginated(path: str, params: dict[str, Any], base_url: str) -> list[dict[str, Any]]:
    """Boucle sur toutes les pages d'un endpoint paginé et agrège les résultats.

    Args:
        path: chemin de la route paginée.
        params: filtres à appliquer (hors page/per_page, gérés ici).
        base_url: racine de l'API.

    Returns:
        La liste complète des éléments, toutes pages confondues.
    """
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = _get_json(
            path, {**params, "page": page, "per_page": MAX_PER_PAGE}, base_url
        )
        results.extend(payload["results"])
        if page >= payload["total_pages"]:
            break
        page += 1
    return results


def fetch_tournees(
    date: str | None = None,
    transporteur_id: int | None = None,
    base_url: str = TRANSFLOW_API_URL,
) -> list[dict[str, Any]]:
    """Récupère toutes les tournées, avec filtres optionnels.

    Args:
        date: filtre sur la date de tournée (YYYY-MM-DD), optionnel.
        transporteur_id: filtre sur le transporteur, optionnel.
        base_url: racine de l'API.

    Returns:
        La liste complète des tournées correspondant aux filtres.
    """
    params: dict[str, Any] = {}
    if date:
        params["date"] = date
    if transporteur_id is not None:
        params["transporteur_id"] = transporteur_id
    return _fetch_paginated("/api/tournees", params, base_url)


def fetch_livraisons(
    statut: str | None = None, base_url: str = TRANSFLOW_API_URL
) -> list[dict[str, Any]]:
    """Récupère toutes les livraisons, avec filtre optionnel sur le statut.

    Args:
        statut: filtre sur le statut de livraison, optionnel.
        base_url: racine de l'API.

    Returns:
        La liste complète des livraisons correspondant au filtre.
    """
    params: dict[str, Any] = {}
    if statut:
        params["statut"] = statut
    return _fetch_paginated("/api/livraisons", params, base_url)
