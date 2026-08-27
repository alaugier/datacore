"""Authentification et autorisation par clé API pour l'Omega Data API (C12).

Deux dépendances FastAPI : `get_current_principal` (authentification
seule — toute clé API valide) et `require_internal` (autorisation —
réservé aux rôles internes, exclut les référents clients externes).
"""
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from datacore.api.config import API_KEYS, Principal, Role

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_principal(api_key: str | None = Security(_api_key_header)) -> Principal:
    """Résout la clé API reçue en un `Principal` (rôle + périmètre client).

    Args:
        api_key: valeur de l'en-tête `X-API-Key`.

    Returns:
        Le `Principal` correspondant à la clé.

    Raises:
        HTTPException: 401 si la clé est absente ou invalide.
    """
    if api_key is None or api_key not in API_KEYS:
        raise HTTPException(
            status_code=401, detail="Clé API manquante ou invalide (en-tête X-API-Key)"
        )
    return API_KEYS[api_key]


def require_internal(principal: Principal = Depends(get_current_principal)) -> Principal:
    """Exige un rôle interne (Data Engineer ou Data Analyst).

    Args:
        principal: identité déjà résolue par `get_current_principal`.

    Returns:
        Le `Principal`, si son rôle est autorisé.

    Raises:
        HTTPException: 403 si l'appelant est un référent client externe.
    """
    if principal.role == Role.CLIENT_REFERENT:
        raise HTTPException(
            status_code=403, detail="Réservé aux équipes internes (Data Engineers/Analysts)"
        )
    return principal
