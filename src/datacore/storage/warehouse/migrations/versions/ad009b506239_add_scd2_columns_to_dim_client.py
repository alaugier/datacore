"""add scd2 columns to dim_client

Revision ID: ad009b506239
Revises: 87dcc1313f23
Create Date: 2026-09-21 11:58:43.035956

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ad009b506239'
down_revision: str | Sequence[str] | None = '87dcc1313f23'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajout nullable d'abord : dim_client porte deja des lignes (chargees
    # par C15) et Postgres refuse un ADD COLUMN NOT NULL sans defaut sur
    # une table non vide. Backfill explicite (2022-01-01, meme ancre que
    # DATE_DEBUT dans load_dim_temps.py -- "debut de l'historique connu")
    # puis passage en NOT NULL une fois les 3 lignes existantes couvertes.
    op.add_column(
        'dim_client',
        sa.Column('valid_from', sa.Date(), nullable=True,
                   comment='SCD2 : début de validité de cette version'),
        schema='dimensions',
    )
    op.add_column(
        'dim_client',
        sa.Column('valid_to', sa.Date(), nullable=True,
                   comment='SCD2 : fin de validité, NULL si version courante'),
        schema='dimensions',
    )
    op.add_column(
        'dim_client',
        sa.Column('is_current', sa.Boolean(), nullable=True,
                   comment='SCD2 : version actuellement en vigueur'),
        schema='dimensions',
    )

    op.execute(
        "UPDATE dimensions.dim_client "
        "SET valid_from = '2022-01-01', is_current = true "
        "WHERE valid_from IS NULL"
    )

    op.alter_column('dim_client', 'valid_from', nullable=False, schema='dimensions')
    op.alter_column('dim_client', 'is_current', nullable=False, schema='dimensions')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('dim_client', 'is_current', schema='dimensions')
    op.drop_column('dim_client', 'valid_to', schema='dimensions')
    op.drop_column('dim_client', 'valid_from', schema='dimensions')
