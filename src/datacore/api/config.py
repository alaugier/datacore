"""Configuration de l'API Omega Data (C12) : rôles, clés API et JWT.

Registre statique de clés API à usage pédagogique — sur le même principe
que `TRANSFLOW_API_KEY` dans l'API mock fournie (`api-mock/app.py`). En
conditions réelles, ces clés seraient émises individuellement et stockées
dans un coffre-fort de secrets, pas codées en clair dans le dépôt.

Modèle d'accès par groupe repris de
`docs/architecture/registre_rgpd.md` §4 : Data Engineers (accès complet),
Data Analysts (lecture), référents clients externes (lecture seule,
restreinte à leur propre client — principe de minimisation).

Authentification par JWT (depuis le 19/11/2026, voir
`docs/architecture/evolution_authentification_jwt.md`) : une clé API
ci-dessous n'est plus envoyée directement sur chaque requête -- elle est
échangée une fois contre un jeton signé via `POST /auth/token`
(`auth.py`), qui est ensuite vérifié localement (signature + expiration)
sans relire ce registre. Les clés elles-mêmes ne changent pas de forme
ni de rôle, seul leur usage change.
"""
import enum
import os
from dataclasses import dataclass


class Role(enum.StrEnum):
    """Groupes d'accès définis dans le registre RGPD."""

    DATA_ENGINEER = "data_engineer"
    DATA_ANALYST = "data_analyst"
    CLIENT_REFERENT = "client_referent"


@dataclass(frozen=True)
class Principal:
    """Identité et périmètre d'accès résolus depuis une clé API.

    Attributes:
        role: groupe d'accès (voir Role).
        client: pour un référent client, le nom du client auquel son
            accès est restreint ; None pour les rôles internes (Data
            Engineer/Analyst), qui ne sont pas limités à un client.
    """

    role: Role
    client: str | None = None


API_KEYS: dict[str, Principal] = {
    "omega-data-engineer-2026": Principal(role=Role.DATA_ENGINEER),
    "omega-data-analyst-2026": Principal(role=Role.DATA_ANALYST),
    "omega-norddrive-2026": Principal(role=Role.CLIENT_REFERENT, client="NordDrive"),
    "omega-freshmarket-2026": Principal(role=Role.CLIENT_REFERENT, client="FreshMarket"),
    "omega-mediotex-2026": Principal(role=Role.CLIENT_REFERENT, client="MedioTex"),
}

# JWT (python-jose) -- cle HMAC partagee, un seul service emetteur et
# verificateur (voir annexe securite de la soutenance : RS256 ne se
# justifierait que si plusieurs services independants devaient
# seulement VERIFIER sans jamais emettre). Valeur par defaut
# explicitement non securisee ("changeme...") pour ne jamais faire
# croire a une vraie protection si .env n'est pas charge -- voir
# LAKE_PSEUDONYM_KEY dans config.py (racine) pour le meme principe
# applique au data lake.
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "changeme-dev-only-not-secure")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
# 480 min = 8h, coherent avec l'annexe securite de la soutenance (page 70)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
