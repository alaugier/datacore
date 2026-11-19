"""add monitoring tables for sse debit and scraping metrics (issue #104)

Revision ID: bd4f2d68682a
Revises: a487cd05b8d5
Create Date: 2026-11-17 09:45:04.674929

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bd4f2d68682a'
down_revision: str | Sequence[str] | None = 'a487cd05b8d5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Deux tables dédiées, distinctes de `catalogue_lake` et de
    `gouvernance.journal_operations` -- pas une réutilisation à tout
    prix (issue #104) :

    - `debit_flux_sse` : réutiliser `catalogue_lake` (flux/zone/nb_lignes)
      aurait mélangé deux significations différentes sous la même clé
      (flux, zone) -- le volume cumulé du flux relevé par
      `enregistrer_catalogue()`, et le nombre d'évènements d'une seule
      fenêtre relevé par `sse_consumer.py`. Détecté en vérifiant le
      dashboard Grafana, pas en relisant seulement le code.
    - `scraping_portail` : le scraping est déjà journalisé dans
      `gouvernance.journal_operations` (réutilise C16, voir
      `run_extraction.py`), mais `bi_reader` (le rôle utilisé par
      Grafana) n'a délibérément pas accès au schéma `gouvernance`
      (vérifié : `permission denied for schema gouvernance`, cohérent
      avec `gestion_operationnelle_omega_bi.md` §3.5/§4 -- "préoccupation
      d'exploitation technique, pas un objet d'analyse métier"). Cette
      table duplique le relevé minimal nécessaire à la visualisation,
      sans donner à `bi_reader` accès à `gouvernance` ni en faire un
      objet d'analyse métier -- le journal `gouvernance` reste la trace
      d'audit de référence, inchangé.
    """
    op.create_table(
        'debit_flux_sse',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flux', sa.String(length=50), nullable=False),
        sa.Column('nb_evenements', sa.Integer(), nullable=False,
                   comment="nombre d'évènements reçus pendant cette fenêtre"),
        sa.Column('releve_le', sa.DateTime(), nullable=False,
                   comment='horodatage du dépôt de la fenêtre'),
        sa.PrimaryKeyConstraint('id'),
        schema='monitoring',
    )
    op.create_table(
        'scraping_portail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nb_colis_scrapes', sa.Integer(), nullable=False),
        sa.Column('nb_erreurs_http', sa.Integer(), nullable=False),
        sa.Column('duree_ms', sa.Integer(), nullable=False),
        sa.Column('releve_le', sa.DateTime(), nullable=False,
                   comment="horodatage de l'exécution du scraping"),
        sa.PrimaryKeyConstraint('id'),
        schema='monitoring',
    )

    op.execute("GRANT SELECT ON monitoring.debit_flux_sse TO bi_reader")
    op.execute("GRANT SELECT ON monitoring.scraping_portail TO bi_reader")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('scraping_portail', schema='monitoring')
    op.drop_table('debit_flux_sse', schema='monitoring')
