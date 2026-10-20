"""add monitoring schema for lake observability C20bis

Revision ID: a487cd05b8d5
Revises: 44a800999124
Create Date: 2026-09-25 16:45:55.055572

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a487cd05b8d5'
down_revision: str | Sequence[str] | None = '44a800999124'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS monitoring")

    # Tables en ajout seul (append-only) -- chaque exécution d'un relevé
    # insère une nouvelle ligne plutôt que d'écraser la précédente, pour
    # que Grafana puisse tracer une évolution dans le temps (fraîcheur,
    # volumétrie), pas seulement un dernier état (voir catalogue.py/
    # purge.py, C20/C21, qui alimentent ces tables).
    op.create_table(
        'catalogue_lake',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flux', sa.String(length=50), nullable=False),
        sa.Column('zone', sa.String(length=20), nullable=False,
                   comment='raw, staging ou curated'),
        sa.Column('nb_lignes', sa.BigInteger(), nullable=False),
        sa.Column('derniere_modification', sa.DateTime(), nullable=False,
                   comment='dernier dépôt S3 réel pour ce flux/zone'),
        sa.Column('releve_le', sa.DateTime(), nullable=False,
                   comment="horodatage de l'exécution du catalogue"),
        sa.PrimaryKeyConstraint('id'),
        schema='monitoring',
    )
    op.create_table(
        'purges_lake',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flux', sa.String(length=50), nullable=False),
        sa.Column('nb_partitions_purgees', sa.Integer(), nullable=False),
        sa.Column('execute_le', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='monitoring',
    )
    op.create_table(
        'sante_infrastructure',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('minio_accessible', sa.Boolean(), nullable=False),
        sa.Column('capacite_utilisee_octets', sa.BigInteger(), nullable=True,
                   comment='NULL si MinIO injoignable au moment du relevé'),
        sa.Column('releve_le', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='monitoring',
    )

    # Droits (même principe que exploitation/dimensions/commercial pour
    # bi_reader, C14) -- monitoring est un schéma dédié, distinct de
    # gouvernance qui reste exclu de bi_reader (registre_rgpd_entrepot.md
    # §4 : "préoccupation d'exploitation technique, pas un objet
    # d'analyse métier" -- ce choix n'est pas révisé ici, monitoring est
    # un nouveau schéma, pas une extension de la portée de gouvernance).
    op.execute("GRANT USAGE ON SCHEMA monitoring TO bi_reader")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO bi_reader")
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE datacore IN SCHEMA monitoring "
        "GRANT SELECT ON TABLES TO bi_reader"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sante_infrastructure', schema='monitoring')
    op.drop_table('purges_lake', schema='monitoring')
    op.drop_table('catalogue_lake', schema='monitoring')
    op.execute("DROP SCHEMA IF EXISTS monitoring CASCADE")
