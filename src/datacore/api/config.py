"""Configuration de l'API Omega Data (C12) : rôles et clés API.

Registre statique de clés API à usage pédagogique — sur le même principe
que `TRANSFLOW_API_KEY` dans l'API mock fournie (`api-mock/app.py`). En
conditions réelles, ces clés seraient émises individuellement et stockées
dans un coffre-fort de secrets, pas codées en clair dans le dépôt.

Modèle d'accès par groupe repris de
`docs/architecture/registre_rgpd.md` §4 : Data Engineers (accès complet),
Data Analysts (lecture), référents clients externes (lecture seule,
restreinte à leur propre client — principe de minimisation).
"""
import enum
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
