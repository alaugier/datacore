"""Schéma SQLAlchemy des tables de la base de travail gérées par Alembic (C11).

Modélise les entités que le programme conçoit lui-même pour la base de
travail consolidée : TransFlow (`transporteurs`, `tournees`,
`livraisons`) et les commandes clients nettoyées par C10
(`commandes_clients` / `lignes_commande_clients`). Les tables FluxPro
(créées depuis `data/raw/schema.sql`, issue #7) et
`historique_expeditions` (créées depuis `sql/historique_schema.sql`,
C9) restent hors du périmètre Alembic : ce sont des schémas déjà
fournis ou déjà créés, pas une modélisation MERISE de notre fait — voir
`docs/architecture/modelisation_merise.md` pour la vue d'ensemble
complète (y compris ces tables pré-existantes) et la justification de
ce découpage.

Utilise SQLAlchemy Core (`Table`/`MetaData`), pas l'ORM déclaratif : le
reste du code du projet (`datacore.ingestion`, `datacore.processing`)
interroge la base directement en SQL via `psycopg2`, sans couche ORM ;
ce module ne sert qu'à décrire le schéma pour Alembic.

Historique de normalisation (26/08/2026, voir
`docs/architecture/modelisation_merise.md` §7) : la première version de
ce schéma violait la 2NF (`commandes_clients` plate) et la 3NF
(`livraisons.statut` transitivement dépendant de `heure_reelle`).
Corrigé après vérification empirique des dépendances fonctionnelles en
jeu.
"""
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
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

# `statut` a été retiré (26/08/2026) : dépendance transitive vérifiée
# empiriquement (heure_reelle renseignée <=> statut = 'Livree', sur les
# 1100 lignes, sans exception -- violation de 3NF). Remplacé par la vue
# `livraisons_avec_statut` (créée dans la migration via op.execute, pas
# modélisable comme Table SQLAlchemy classique), qui recalcule statut à
# la lecture plutôt que de le stocker en doublon.
livraisons = Table(
    "livraisons",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tournee_id", Integer, ForeignKey("tournees.id"), nullable=False),
    # tracking_number : clé métier de rapprochement avec
    # expeditions.tracking_number (FluxPro) -- pas de contrainte FK
    # formelle, les deux tables proviennent de systèmes distincts (voir
    # topographie des données §3.2). Rapprochement vérifié fiable à
    # 100 % (1100/1100) -- voir modelisation_merise.md §3.1.
    Column("tracking_number", String(20), nullable=False),
    # Donnée personnelle (voir docs/architecture/registre_rgpd.md) :
    # adresse de livraison du destinataire.
    Column("adresse_livraison", String(200)),
    Column("heure_estimee", String(10)),
    Column("heure_reelle", String(10)),
)

# En-tête de commande client (26/08/2026, remplace l'ancienne table
# plate `commandes_clients` qui violait la 2NF : date_commande et
# entrepot ne dépendaient que de (client, commande_id), pas du sku).
commandes_clients = Table(
    "commandes_clients",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("client", String(50), nullable=False),
    Column("commande_id", String(30), nullable=False),
    Column("date_commande", Date, nullable=False),
    Column("entrepot", String(20)),
    UniqueConstraint("client", "commande_id", name="uq_commandes_clients_client_commande"),
)

# Lignes de commande client (une par produit commandé). `libelle_produit`,
# `poids_kg` et `chaine_froid_requise` ont été retirés (26/08/2026) :
# vérifiés empiriquement comme entièrement dérivables de `produits` côté
# FluxPro via `sku` (0 écart sur 30 sku x 3 clients), donc redondants --
# violation de 2NF corrigée en s'appuyant sur le référentiel produit
# existant plutôt qu'en dupliquant l'information.
lignes_commande_clients = Table(
    "lignes_commande_clients",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("commande_client_id", Integer, ForeignKey("commandes_clients.id"), nullable=False),
    # sku : clé métier vers produits.sku (FluxPro) -- pas de FK formelle
    # possible : produits.sku n'est pas contraint UNIQUE dans le schéma
    # fourni (seul produits.id est PK). Intégrité vérifiée empiriquement
    # (0 orphelin sur les 30 sku des 3 fichiers clients).
    Column("sku", String(20), nullable=False),
    Column("quantite", Integer, nullable=False),
    UniqueConstraint(
        "commande_client_id", "sku", name="uq_lignes_commande_clients_commande_sku"
    ),
)
