"""Omega Data API (C12) : expose le jeu de données consolidé (C8-C11) aux
équipes BI et data science, avec authentification et autorisation par groupe.

Authentification par clé API (en-tête `X-API-Key`) ; autorisation par
rôle (Data Engineer, Data Analyst, référent client externe) — modèle
d'accès défini dans `docs/architecture/registre_rgpd.md` §4 : les
référents clients externes sont systématiquement restreints à leur
propre client, et n'ont pas accès aux données de transport (livraisons),
qui portent des données personnelles (chauffeur, adresse) hors de leur
périmètre.

Lancement :
    uvicorn datacore.api.main:app --reload

Documentation interactive (spécification OpenAPI générée automatiquement) :
    http://127.0.0.1:8000/docs
"""
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query

from datacore.api import repository
from datacore.api.auth import get_current_principal, require_internal
from datacore.api.config import Principal, Role
from datacore.api.db import get_db
from datacore.api.schemas import (
    CommandeClient,
    LigneCommandeClient,
    Livraison,
    StatutLivraison,
    TauxServiceClient,
)

app = FastAPI(
    title="Omega Data API",
    description=(
        "API REST du programme DATA CORE (C12) : accès sécurisé au jeu de "
        "données consolidé (commandes clients, livraisons, indicateurs de "
        "performance). Voir docs/architecture/registre_rgpd.md pour le "
        "modèle d'accès par groupe."
    ),
    version="1.0.0",
)


@app.get("/health", tags=["Système"])
def health() -> dict[str, str]:
    """Vérifie la disponibilité du service (sans authentification)."""
    return {"status": "ok", "service": "Omega Data API"}


def _resolve_client_scope(principal: Principal, requested_client: str | None) -> str | None:
    """Applique le périmètre client d'un référent, sans jamais l'étendre.

    Args:
        principal: identité de l'appelant.
        requested_client: client demandé en paramètre de requête, le cas échéant.

    Returns:
        Pour un référent client : toujours son propre client (le
        paramètre demandé est ignoré, pas seulement validé). Pour un
        rôle interne : le client demandé, tel quel (`None` = pas de filtre).
    """
    if principal.role == Role.CLIENT_REFERENT:
        return principal.client
    return requested_client


@app.get(
    "/commandes-clients", response_model=list[CommandeClient], tags=["Commandes clients"]
)
def get_commandes_clients(
    client: str | None = Query(
        default=None,
        description="Filtre sur un client (ignoré pour un référent, toujours restreint au sien)",
    ),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    db: Any = Depends(get_db),
) -> list[dict[str, Any]]:
    """Liste les commandes clients consolidées (C10/C11), restreintes au périmètre de l'appelant."""
    scoped_client = _resolve_client_scope(principal, client)
    return repository.list_commandes_clients(db, client=scoped_client, limit=limit, offset=offset)


@app.get(
    "/commandes-clients/{commande_client_id}/lignes",
    response_model=list[LigneCommandeClient],
    tags=["Commandes clients"],
)
def get_lignes_commande_client(
    commande_client_id: int,
    principal: Principal = Depends(get_current_principal),
    db: Any = Depends(get_db),
) -> list[dict[str, Any]]:
    """Liste les lignes d'une commande client, restreint au périmètre de l'appelant."""
    commande = repository.get_commande_client(db, commande_client_id)
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    if principal.role == Role.CLIENT_REFERENT and commande["client"] != principal.client:
        raise HTTPException(status_code=403, detail="Hors de votre périmètre client")
    return repository.list_lignes_commande_client(db, commande_client_id)


@app.get("/livraisons", response_model=list[Livraison], tags=["Livraisons"])
def get_livraisons(
    statut: StatutLivraison | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_internal),
    db: Any = Depends(get_db),
) -> list[dict[str, Any]]:
    """Liste les livraisons TransFlow — équipes internes uniquement (données de transport)."""
    return repository.list_livraisons(db, statut=statut, limit=limit, offset=offset)


@app.get("/kpis/taux-service", response_model=list[TauxServiceClient], tags=["KPIs"])
def get_taux_service(
    client: str | None = Query(default=None),
    principal: Principal = Depends(get_current_principal),
    db: Any = Depends(get_db),
) -> list[dict[str, Any]]:
    """Taux de service (livraisons à l'heure) par client, restreint au périmètre de l'appelant."""
    scoped_client = _resolve_client_scope(principal, client)
    return repository.taux_service_par_client(db, client=scoped_client)
