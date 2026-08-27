-- Schéma SQL de la base de travail consolidée (C11) — document de
-- référence, à titre pédagogique/documentaire.
--
-- Reprend exactement le schéma modélisé dans
-- src/datacore/storage/staging/models.py et créé via Alembic
-- (src/datacore/storage/staging/migrations/) : ce fichier n'est PAS
-- utilisé pour créer la base (Alembic gère cette responsabilité), il
-- sert de référence lisible sans dépendance à SQLAlchemy/Python — voir
-- docs/architecture/modelisation_merise.md pour le MCD complet et la
-- justification des choix de modélisation.
--
-- Cinq tables + une vue, dans l'ordre de création (respecte les
-- dépendances de clés étrangères) :
--   transporteurs -> tournees -> livraisons (+ vue livraisons_avec_statut)
--   commandes_clients -> lignes_commande_clients
--
-- Côté FluxPro (entrepots, clients, produits, commandes,
-- lignes_commande, expeditions, stocks) : schéma FOURNI, voir
-- data/raw/schema.sql (non versionné) et scripts/init_staging_db.sh —
-- pas une modélisation de notre fait, volontairement absent d'ici.
-- Côté historique « système big data » : voir sql/historique_schema.sql (C9).

CREATE TABLE transporteurs (
  id       INTEGER PRIMARY KEY,
  nom      VARCHAR(100) NOT NULL,
  contact  VARCHAR(150)
);

CREATE TABLE tournees (
  id               INTEGER PRIMARY KEY,
  transporteur_id  INTEGER NOT NULL REFERENCES transporteurs(id),
  date             DATE NOT NULL,
  vehicule_id      VARCHAR(20),
  -- Donnée personnelle (voir docs/architecture/registre_rgpd.md) : nom
  -- du chauffeur.
  chauffeur        VARCHAR(100)
);

-- `statut` a été retiré (violation de 3NF : dépendance transitive avec
-- heure_reelle, vérifiée empiriquement à 100 % sur les 1100 lignes —
-- voir docs/architecture/modelisation_merise.md §3.3). Remplacé par la
-- vue livraisons_avec_statut ci-dessous, qui le recalcule à la lecture
-- plutôt que de le stocker en doublon.
CREATE TABLE livraisons (
  id                 INTEGER PRIMARY KEY,
  tournee_id         INTEGER NOT NULL REFERENCES tournees(id),
  -- Clé métier de rapprochement avec expeditions.tracking_number
  -- (FluxPro) -- pas de contrainte FK formelle, deux systèmes
  -- distincts. Rapprochement vérifié fiable à 100 % (1100/1100).
  tracking_number    VARCHAR(20) NOT NULL,
  -- Donnée personnelle (voir docs/architecture/registre_rgpd.md) :
  -- adresse de livraison du destinataire.
  adresse_livraison  VARCHAR(200),
  heure_estimee      VARCHAR(10),
  heure_reelle       VARCHAR(10)
);

CREATE VIEW livraisons_avec_statut AS
SELECT *,
    CASE WHEN heure_reelle IS NOT NULL THEN 'Livree' ELSE 'En cours' END AS statut
FROM livraisons;

-- En-tête de commande client (C10), décomposé depuis une première
-- version plate qui violait la 2NF (voir
-- docs/architecture/modelisation_merise.md §3.4). `id` en SERIAL : à la
-- différence des trois tables précédentes (id TransFlow préservé), C10
-- ne fournit aucun identifiant numérique -- la base le génère.
CREATE TABLE commandes_clients (
  id             SERIAL PRIMARY KEY,
  client         VARCHAR(50) NOT NULL,
  commande_id    VARCHAR(30) NOT NULL,
  date_commande  DATE NOT NULL,
  entrepot       VARCHAR(20),
  UNIQUE (client, commande_id)
);

-- libelle_produit, poids_kg et chaine_froid_requise ont été retirés :
-- vérifiés empiriquement comme entièrement dérivables de produits
-- (FluxPro) via sku, sans le moindre écart (0/30 sku x 3 clients).
CREATE TABLE lignes_commande_clients (
  id                  SERIAL PRIMARY KEY,
  commande_client_id  INTEGER NOT NULL REFERENCES commandes_clients(id),
  -- Clé métier vers produits.sku (FluxPro) -- pas de FK formelle
  -- possible : produits.sku n'est pas contraint UNIQUE dans le schéma
  -- fourni (seul produits.id est clé primaire). Intégrité vérifiée
  -- empiriquement (0 orphelin sur 3593 lignes importées).
  sku                 VARCHAR(20) NOT NULL,
  quantite            INTEGER NOT NULL,
  UNIQUE (commande_client_id, sku)
);
