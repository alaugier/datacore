"""Modèles Pydantic des réponses de l'Omega Data API (C12).

Génèrent automatiquement la spécification OpenAPI de l'API (voir
`/openapi.json` et `/docs` une fois le service lancé).
"""
import datetime

from pydantic import BaseModel, Field


class CommandeClient(BaseModel):
    """En-tête d'une commande client consolidée (C10/C11)."""

    id: int
    client: str
    commande_id: str = Field(
        description="Identifiant de commande propre au client (pas une clé FluxPro)"
    )
    date_commande: datetime.date
    entrepot: str | None = None


class LigneCommandeClient(BaseModel):
    """Ligne d'une commande client, enrichie du référentiel produit FluxPro via `sku`."""

    id: int
    sku: str
    libelle_produit: str
    quantite: int
    poids_kg: float | None = None
    temperature_dirigee: bool | None = None


class Livraison(BaseModel):
    """Livraison TransFlow, avec `statut` dérivé de `heure_reelle` (voir C11 §3.3)."""

    id: int
    tournee_id: int
    tracking_number: str
    heure_estimee: str | None = None
    heure_reelle: str | None = None
    statut: str


class TauxServiceClient(BaseModel):
    """Taux de service (livraisons à l'heure) agrégé par client, calculé sur FluxPro."""

    client: str
    nb_expeditions: int
    taux_service_pct: float
