"""Schéma SQLAlchemy de l'entrepôt OMEGA BI, versionné via Alembic (C14).

Implémente la modélisation en étoile/flocon conçue en C13 (voir
`docs/architecture/modelisation_omega_bi.md`) dans une base Postgres
distincte (`OMEGA_BI_DB`, même instance que la base de staging — voir
`datacore.ingestion.config`), organisée en 3 schémas Postgres :

- `dimensions` : les 6 dimensions conformées, partagées entre les deux
  datamarts (`Dim_Client`, `Dim_Site`, `Dim_Produit`, `Dim_Categorie`,
  `Dim_Temps`, `Dim_Transporteur`).
- `exploitation` : `Fait_Expedition`, `Fait_Stock` (datamart Exploitation).
- `commercial` : `Fait_Commande` (datamart Commercial).

Cette séparation physique en schémas rend tangible le principe bottom-up
par datamarts avec dimensions conformées (C13 §1) : chaque datamart est
un schéma Postgres indépendant, qui référence les dimensions partagées
par clé étrangère inter-schéma.

`Dim_Client` ne porte pas encore les colonnes `valid_from`/`valid_to`/
`is_current` : elles seront ajoutées par une migration Alembic
additionnelle en C17 (SCD2), conformément au choix déjà documenté en
C13 §6.1 (clé de substitution posée dès maintenant pour que cet ajout
reste non disruptif).

Utilise SQLAlchemy Core (`Table`/`MetaData`), pas l'ORM déclaratif, sur
le même principe que `datacore.storage.staging.models` : ce module ne
sert qu'à décrire le schéma pour Alembic, le chargement (C15) interroge
la base directement en SQL via `psycopg2`.
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)

metadata = MetaData()

# --- schéma "dimensions" (dimensions conformées, partagées) ---------------

dim_client = Table(
    "dim_client",
    metadata,
    Column("client_key", Integer, primary_key=True),
    Column("client_id", Integer, nullable=False, comment="clé naturelle FluxPro"),
    Column("code", String(30), nullable=False),
    Column("nom", String(100), nullable=False),
    Column("secteur", String(100)),
    schema="dimensions",
)

dim_site = Table(
    "dim_site",
    metadata,
    Column("site_key", Integer, primary_key=True),
    Column("entrepot_id", Integer, nullable=False, comment="clé naturelle FluxPro"),
    Column("code", String(20), nullable=False),
    Column("nom", String(100), nullable=False),
    Column("ville", String(100), nullable=False),
    Column("capacite_palettes", Integer),
    schema="dimensions",
)

# Dimension à grain réduit (« shrunken dimension »), nécessaire car
# historique_expeditions ne fournit qu'une catégorie, jamais un SKU
# précis -- voir modelisation_omega_bi.md §6.3.
dim_categorie = Table(
    "dim_categorie",
    metadata,
    Column("categorie_key", Integer, primary_key=True),
    Column("libelle", String(50), nullable=False, unique=True),
    schema="dimensions",
)

dim_produit = Table(
    "dim_produit",
    metadata,
    Column("produit_key", Integer, primary_key=True),
    Column("produit_id", Integer, nullable=False, comment="clé naturelle FluxPro"),
    Column("sku", String(20), nullable=False),
    Column("libelle", String(150), nullable=False),
    Column("poids_kg", Numeric(6, 2)),
    Column("temperature_dirigee", Boolean),
    Column(
        "categorie_key",
        Integer,
        ForeignKey("dimensions.dim_categorie.categorie_key"),
        nullable=False,
    ),
    schema="dimensions",
)

# Dimension calendaire générée (pas issue d'une table source) : date_key
# est une clé signifiante YYYYMMDD, pas une SERIAL -- permet des
# comparaisons/plages de dates sans jointure.
dim_temps = Table(
    "dim_temps",
    metadata,
    Column("date_key", Integer, primary_key=True, comment="YYYYMMDD"),
    Column("date_complete", Date, nullable=False, unique=True),
    Column("annee", Integer, nullable=False),
    Column("trimestre", Integer, nullable=False),
    Column("mois", Integer, nullable=False),
    Column("nom_mois", String(20), nullable=False),
    Column("jour_semaine", Integer, nullable=False),
    Column("numero_semaine", Integer, nullable=False),
    Column("est_weekend", Boolean, nullable=False),
    schema="dimensions",
)

# transporteur_id nullable : absent pour le membre "Inconnu" qui couvre
# les lignes de Fait_Expedition issues de l'historique (pas de colonne
# transporteur dans cette source) -- voir modelisation_omega_bi.md §6.5.
# `contact` (donnée personnelle, voir registre_rgpd.md) volontairement
# exclu : RGPD by design, aucun usage décisionnel.
dim_transporteur = Table(
    "dim_transporteur",
    metadata,
    Column("transporteur_key", Integer, primary_key=True),
    Column("transporteur_id", Integer, comment="clé naturelle, absente pour le membre Inconnu"),
    Column("nom", String(100), nullable=False),
    schema="dimensions",
)

# --- schéma "exploitation" (datamart Exploitation) -------------------------

# Deux sources à grain différent alimentent ce fait (FluxPro/TransFlow et
# historique) -- voir modelisation_omega_bi.md §5.1 pour le détail des
# règles de transformation et des clés nullables selon la source.
fait_expedition = Table(
    "fait_expedition",
    metadata,
    Column("expedition_key", Integer, primary_key=True),
    Column("client_key", Integer, ForeignKey("dimensions.dim_client.client_key")),
    Column(
        "site_key", Integer, ForeignKey("dimensions.dim_site.site_key"), nullable=False
    ),
    Column(
        "categorie_key",
        Integer,
        ForeignKey("dimensions.dim_categorie.categorie_key"),
        nullable=False,
    ),
    Column(
        "date_key", Integer, ForeignKey("dimensions.dim_temps.date_key"), nullable=False
    ),
    Column(
        "transporteur_key",
        Integer,
        ForeignKey("dimensions.dim_transporteur.transporteur_key"),
    ),
    Column("tracking_number", String(20), comment="dimension dégénérée, absente côté historique"),
    Column("source_systeme", String(20), nullable=False, comment="FluxPro_TransFlow ou Historique"),
    Column("poids_kg", Numeric(8, 2)),
    Column("delai_livraison_jours", Integer),
    Column("cout_transport_eur", Numeric(8, 2), comment="absent côté FluxPro/TransFlow"),
    Column("statut", String(30), nullable=False),
    Column("livre_a_lheure", Boolean),
    schema="exploitation",
)

# Periodic snapshot fact (grain jour) -- voir modelisation_omega_bi.md
# §5.2 : le jeu de données pédagogique ne fournit qu'un seul instantané
# aujourd'hui, mais le modèle est prêt pour un historique quotidien.
fait_stock = Table(
    "fait_stock",
    metadata,
    Column("stock_key", Integer, primary_key=True),
    Column(
        "site_key", Integer, ForeignKey("dimensions.dim_site.site_key"), nullable=False
    ),
    Column(
        "produit_key",
        Integer,
        ForeignKey("dimensions.dim_produit.produit_key"),
        nullable=False,
    ),
    Column(
        "date_key", Integer, ForeignKey("dimensions.dim_temps.date_key"), nullable=False
    ),
    Column("quantite_stock", Integer, nullable=False),
    UniqueConstraint("site_key", "produit_key", "date_key", name="uq_fait_stock_grain"),
    schema="exploitation",
)

# --- schéma "commercial" (datamart Commercial) ------------------------------

# Grain ligne de commande FluxPro (commandes/lignes_commande) --
# commandes_clients volontairement hors périmètre, voir
# modelisation_omega_bi.md §6.1.
fait_commande = Table(
    "fait_commande",
    metadata,
    Column("commande_ligne_key", Integer, primary_key=True),
    Column(
        "client_key",
        Integer,
        ForeignKey("dimensions.dim_client.client_key"),
        nullable=False,
    ),
    Column(
        "site_key", Integer, ForeignKey("dimensions.dim_site.site_key"), nullable=False
    ),
    Column(
        "produit_key",
        Integer,
        ForeignKey("dimensions.dim_produit.produit_key"),
        nullable=False,
    ),
    Column(
        "date_key", Integer, ForeignKey("dimensions.dim_temps.date_key"), nullable=False
    ),
    Column("commande_id", String(30), nullable=False, comment="dimension dégénérée, clé FluxPro"),
    Column("quantite_commandee", Integer, nullable=False),
    Column("poids_ligne", Numeric(8, 2)),
    Column("statut_commande", String(30), nullable=False),
    schema="commercial",
)
