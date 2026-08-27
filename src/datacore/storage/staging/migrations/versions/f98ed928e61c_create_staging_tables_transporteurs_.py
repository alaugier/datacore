"""create staging tables (transporteurs, tournees, livraisons,
commandes_clients, lignes_commande_clients)

Revision ID: f98ed928e61c
Revises:
Create Date: 2026-08-26 16:18:40.287322

Ne gère que les tables modélisées par C11 (voir
src/datacore/storage/staging/models.py). Les tables FluxPro
(data/raw/schema.sql, issue #7) et historique_expeditions
(sql/historique_schema.sql, C9) sont hors du périmètre Alembic : les
`op.drop_table(...)` / `op.create_table(...)` que --autogenerate
proposait pour elles (parce qu'elles n'apparaissent pas dans
`target_metadata`) ont été retirés à la main -- elles ne doivent jamais
être créées ni supprimées par cette migration.

Schéma normalisé le 26/08/2026 après vérification empirique des
dépendances fonctionnelles (voir docs/architecture/modelisation_merise.md
§7) : `livraisons.statut` (dépendance transitive avec `heure_reelle`,
3NF) est remplacée par une vue `livraisons_avec_statut` qui la recalcule
à la lecture, sans redondance stockée ; `commandes_clients` est scindée
en en-tête + `lignes_commande_clients` (2NF), les colonnes
`libelle_produit`/`poids_kg`/`chaine_froid_requise` étant entièrement
dérivables de `produits` (FluxPro) via `sku`.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f98ed928e61c'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('commandes_clients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client', sa.String(length=50), nullable=False),
    sa.Column('commande_id', sa.String(length=30), nullable=False),
    sa.Column('date_commande', sa.Date(), nullable=False),
    sa.Column('entrepot', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('client', 'commande_id', name='uq_commandes_clients_client_commande')
    )
    op.create_table('transporteurs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(length=100), nullable=False),
    sa.Column('contact', sa.String(length=150), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lignes_commande_clients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('commande_client_id', sa.Integer(), nullable=False),
    sa.Column('sku', sa.String(length=20), nullable=False),
    sa.Column('quantite', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['commande_client_id'], ['commandes_clients.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('commande_client_id', 'sku', name='uq_lignes_commande_clients_commande_sku')
    )
    op.create_table('tournees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transporteur_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('vehicule_id', sa.String(length=20), nullable=True),
    sa.Column('chauffeur', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['transporteur_id'], ['transporteurs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('livraisons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tournee_id', sa.Integer(), nullable=False),
    sa.Column('tracking_number', sa.String(length=20), nullable=False),
    sa.Column('adresse_livraison', sa.String(length=200), nullable=True),
    sa.Column('heure_estimee', sa.String(length=10), nullable=True),
    sa.Column('heure_reelle', sa.String(length=10), nullable=True),
    sa.ForeignKeyConstraint(['tournee_id'], ['tournees.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # Vue plutot que colonne stockee : elimine completement la redondance
    # (pas seulement le risque d'incoherence qu'aurait laisse une colonne
    # generee STORED). Choix documente dans modelisation_merise.md §7.2.
    op.execute("""
        CREATE VIEW livraisons_avec_statut AS
        SELECT *,
            CASE WHEN heure_reelle IS NOT NULL THEN 'Livree' ELSE 'En cours' END AS statut
        FROM livraisons
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP VIEW IF EXISTS livraisons_avec_statut")
    op.drop_table('livraisons')
    op.drop_table('tournees')
    op.drop_table('lignes_commande_clients')
    op.drop_table('transporteurs')
    op.drop_table('commandes_clients')
