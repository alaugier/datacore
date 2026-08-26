"""Schéma SQLAlchemy des tables de la base de travail gérées par Alembic (C11).

Modélise les entités que le programme conçoit lui-même pour la base de
travail consolidée : TransFlow (`transporteurs`, `tournees`,
`livraisons`) et les commandes clients nettoyées par C10
(`commandes_clients`). Les tables FluxPro (créées depuis
`data/raw/schema.sql`, issue #7) et `historique_expeditions` (créées
depuis `sql/historique_schema.sql`, C9) restent hors du périmètre
Alembic : ce sont des schémas déjà fournis ou déjà créés, pas une
modélisation MERISE de notre fait — voir
`docs/architecture/modelisation_merise.md` pour la vue d'ensemble
complète (y compris ces tables pré-existantes) et la justification de
ce découpage.

Utilise SQLAlchemy Core (`Table`/`MetaData`), pas l'ORM déclaratif : le
reste du code du projet (`datacore.ingestion`, `datacore.processing`)
interroge la base directement en SQL via `psycopg2`, sans couche ORM ;
ce module ne sert qu'à décrire le schéma pour Alembic.
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
)

metadata = MetaData()

transporteurs = Table(
    "transporteurs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nom", String(100), nullable=False),
    Column("contact", String(150)),
)

tournees = Table(
    "tournees",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("transporteur_id", Integer, ForeignKey("transporteurs.id"), nullable=False),
    Column("date", Date, nullable=False),
    Column("vehicule_id", String(20)),
    # Donnée personnelle (voir docs/architecture/registre_rgpd.md) : nom
    # du chauffeur. Colonne dédiée pour permettre un tri/anonymisation
    # ciblé sans toucher au reste de la ligne.
    Column("chauffeur", String(100)),
)

livraisons = Table(
    "livraisons",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tournee_id", Integer, ForeignKey("tournees.id"), nullable=False),
    # tracking_number : clé métier de rapprochement avec
    # expeditions.tracking_number (FluxPro) -- pas de contrainte FK
    # formelle, les deux tables proviennent de systèmes distincts (voir
    # topographie des données §3.2).
    Column("tracking_number", String(20), nullable=False),
    # Donnée personnelle (voir docs/architecture/registre_rgpd.md) :
    # adresse de livraison du destinataire.
    Column("adresse_livraison", String(200)),
    Column("statut", String(30)),
    Column("heure_estimee", String(10)),
    Column("heure_reelle", String(10)),
)

commandes_clients = Table(
    "commandes_clients",
    metadata,
    Column("id", Integer, primary_key=True),
    # Grain (client, commande_id, sku) : clé naturelle du jeu de données
    # consolidé produit par C10 (voir
    # src/datacore/processing/clients_cleaning.py). Pas de clé unique
    # SQL formelle ici : le dédoublonnage est déjà garanti en amont par
    # clean_and_aggregate(), avant l'import.
    Column("client", String(50), nullable=False),
    Column("commande_id", String(30), nullable=False),
    Column("date_commande", Date, nullable=False),
    Column("sku", String(20), nullable=False),
    Column("libelle_produit", String(150)),
    Column("quantite", Integer, nullable=False),
    Column("poids_kg", Numeric(8, 3)),
    Column("entrepot", String(20)),
    Column("chaine_froid_requise", Boolean),
)
