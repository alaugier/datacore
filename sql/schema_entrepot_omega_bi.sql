-- Schéma SQL complet de l'entrepôt OMEGA BI — document de référence,
-- à titre pédagogique/documentaire.
--
-- Reprend exactement le schéma modélisé dans
-- src/datacore/storage/warehouse/models.py et créé via Alembic
-- (src/datacore/storage/warehouse/migrations/, config
-- alembic_omega_bi.ini) : ce fichier n'est PAS utilisé pour créer la
-- base (Alembic gère cette responsabilité), il sert de référence
-- lisible sans dépendance à SQLAlchemy/Python — généré à partir d'un
-- schéma réel (`pg_dump --schema-only`) puis réorganisé et annoté pour
-- rester lisible, voir §7 pour la procédure de mise à jour.
--
-- Croisé avec docs/architecture/modelisation_omega_bi.md (C13, MCD
-- complet et justifications de modélisation), creation_entrepot_omega_bi.md
-- (C14), pipelines_etl_omega_bi.md (C15),
-- historisation_dim_client_scd2.md (C17) et
-- gestion_operationnelle_omega_bi.md / registre_rgpd_entrepot.md (C16).
--
-- 4 schémas Postgres, dans l'ordre de dépendance :
--   dimensions   -- 6 dimensions conformées, partagées entre datamarts
--   exploitation -- Fait_Expedition, Fait_Stock + 2 vues SLA
--   commercial   -- Fait_Commande
--   gouvernance  -- journal_operations + 1 vue de suivi (C16)

-- ============================================================
-- Schéma "dimensions" — dimensions conformées
-- ============================================================

CREATE SCHEMA dimensions;

-- Dimension à grain réduit (« shrunken dimension »), nécessaire car
-- historique_expeditions (staging) ne fournit qu'une catégorie, jamais
-- un SKU précis — voir modelisation_omega_bi.md §6.3.
CREATE TABLE dimensions.dim_categorie (
  categorie_key  SERIAL PRIMARY KEY,
  libelle        VARCHAR(50) NOT NULL UNIQUE
);

-- SCD2 (Kimball, C17) : la seule dimension historisée du modèle, jamais
-- tronquée par le pipeline ETL (voir load_warehouse.truncate_warehouse).
-- `nom`/`secteur` sont les attributs suivis -- `clients` (FluxPro) n'a
-- ni adresse ni contrat, voir historisation_dim_client_scd2.md §1.
CREATE TABLE dimensions.dim_client (
  client_key  SERIAL PRIMARY KEY,
  client_id   INTEGER NOT NULL,        -- clé naturelle FluxPro
  code        VARCHAR(30) NOT NULL,    -- clé métier, jamais historisée (SCD1 implicite)
  nom         VARCHAR(100) NOT NULL,   -- SCD2 : attribut suivi
  secteur     VARCHAR(100),            -- SCD2 : attribut suivi
  valid_from  DATE NOT NULL,           -- SCD2 : début de validité de cette version
  valid_to    DATE,                    -- SCD2 : fin de validité, NULL si version courante
  is_current  BOOLEAN NOT NULL         -- SCD2 : version actuellement en vigueur
);

CREATE TABLE dimensions.dim_site (
  site_key           SERIAL PRIMARY KEY,
  entrepot_id        INTEGER NOT NULL,       -- clé naturelle FluxPro
  code               VARCHAR(20) NOT NULL,
  nom                VARCHAR(100) NOT NULL,
  ville              VARCHAR(100) NOT NULL,
  capacite_palettes  INTEGER
);

CREATE TABLE dimensions.dim_produit (
  produit_key           SERIAL PRIMARY KEY,
  produit_id            INTEGER NOT NULL,    -- clé naturelle FluxPro
  sku                   VARCHAR(20) NOT NULL,
  libelle               VARCHAR(150) NOT NULL,
  poids_kg              DECIMAL(6,2),
  temperature_dirigee   BOOLEAN,
  categorie_key         INTEGER NOT NULL REFERENCES dimensions.dim_categorie(categorie_key)
);

-- Dimension calendaire générée (pas issue d'une table source) :
-- date_key est une clé signifiante YYYYMMDD, pas une SERIAL -- permet
-- des comparaisons/plages de dates sans jointure. Chargée par
-- load_dim_temps.py (C14), pas tronquée par l'ETL (C15).
CREATE TABLE dimensions.dim_temps (
  date_key         INTEGER PRIMARY KEY,   -- YYYYMMDD
  date_complete    DATE NOT NULL UNIQUE,
  annee            INTEGER NOT NULL,
  trimestre        INTEGER NOT NULL,
  mois             INTEGER NOT NULL,
  nom_mois         VARCHAR(20) NOT NULL,
  jour_semaine     INTEGER NOT NULL,
  numero_semaine   INTEGER NOT NULL,
  est_weekend      BOOLEAN NOT NULL
);

-- transporteur_id nullable : absent pour le membre "Inconnu" qui couvre
-- les lignes de Fait_Expedition issues de l'historique (pas de colonne
-- transporteur dans cette source). `contact` (donnée personnelle, voir
-- registre_rgpd.md) volontairement exclu : RGPD by design, voir
-- modelisation_omega_bi.md §6.5.
CREATE TABLE dimensions.dim_transporteur (
  transporteur_key  SERIAL PRIMARY KEY,
  transporteur_id   INTEGER,               -- clé naturelle, absente pour le membre Inconnu
  nom               VARCHAR(100) NOT NULL
);

-- ============================================================
-- Schéma "exploitation" — datamart Exploitation (transport, stock)
-- ============================================================

CREATE SCHEMA exploitation;

-- Deux sources alimentent ce fait, à des grains de détail différents --
-- voir modelisation_omega_bi.md §5.1 pour le détail des règles de
-- transformation (client_key/transporteur_key nullables selon la
-- source, cout_transport_eur absent côté FluxPro/TransFlow).
CREATE TABLE exploitation.fait_expedition (
  expedition_key         SERIAL PRIMARY KEY,
  client_key              INTEGER REFERENCES dimensions.dim_client(client_key),
  site_key                INTEGER NOT NULL REFERENCES dimensions.dim_site(site_key),
  categorie_key            INTEGER NOT NULL REFERENCES dimensions.dim_categorie(categorie_key),
  date_key                 INTEGER NOT NULL REFERENCES dimensions.dim_temps(date_key),
  transporteur_key         INTEGER REFERENCES dimensions.dim_transporteur(transporteur_key),
  tracking_number          VARCHAR(20),          -- dimension dégénérée, absente côté historique
  source_systeme           VARCHAR(20) NOT NULL, -- FluxPro_TransFlow ou Historique
  poids_kg                 DECIMAL(8,2),
  delai_livraison_jours    INTEGER,
  cout_transport_eur       DECIMAL(8,2),         -- absent côté FluxPro/TransFlow
  statut                   VARCHAR(30) NOT NULL,
  livre_a_lheure           BOOLEAN               -- NULL pour l'historique, voir pipelines_etl_omega_bi.md §2.2
);

-- Periodic snapshot fact (grain jour) -- voir modelisation_omega_bi.md
-- §5.2 : le jeu de données pédagogique ne fournit qu'un seul instantané
-- aujourd'hui, mais le modèle est prêt pour un historique quotidien.
CREATE TABLE exploitation.fait_stock (
  stock_key       SERIAL PRIMARY KEY,
  site_key        INTEGER NOT NULL REFERENCES dimensions.dim_site(site_key),
  produit_key     INTEGER NOT NULL REFERENCES dimensions.dim_produit(produit_key),
  date_key        INTEGER NOT NULL REFERENCES dimensions.dim_temps(date_key),
  quantite_stock  INTEGER NOT NULL,
  CONSTRAINT uq_fait_stock_grain UNIQUE (site_key, produit_key, date_key)
);

-- Vues d'indicateurs de service (C16) -- voir
-- gestion_operationnelle_omega_bi.md §3. Héritent automatiquement des
-- droits de lecture bi_reader via ALTER DEFAULT PRIVILEGES (§7).

CREATE VIEW exploitation.v_taux_service_client AS
SELECT
    dc.nom AS client,
    count(*) AS nb_expeditions,
    round(
        100.0 * sum(CASE WHEN fe.livre_a_lheure THEN 1 ELSE 0 END) / count(*),
        1
    ) AS taux_service_pct
FROM exploitation.fait_expedition fe
JOIN dimensions.dim_client dc ON dc.client_key = fe.client_key
WHERE fe.source_systeme = 'FluxPro_TransFlow' AND fe.livre_a_lheure IS NOT NULL
GROUP BY dc.nom;

CREATE VIEW exploitation.v_delai_moyen_transporteur AS
SELECT
    dt.nom AS transporteur,
    count(*) AS nb_expeditions,
    round(avg(fe.delai_livraison_jours)::numeric, 1) AS delai_moyen_jours
FROM exploitation.fait_expedition fe
JOIN dimensions.dim_transporteur dt ON dt.transporteur_key = fe.transporteur_key
WHERE fe.delai_livraison_jours IS NOT NULL
GROUP BY dt.nom;

CREATE VIEW exploitation.v_stock_disponible_site AS
SELECT
    ds.nom AS entrepot,
    sum(fs.quantite_stock) AS quantite_totale,
    count(DISTINCT fs.produit_key) AS nb_references
FROM exploitation.fait_stock fs
JOIN dimensions.dim_site ds ON ds.site_key = fs.site_key
GROUP BY ds.nom;

-- ============================================================
-- Schéma "commercial" — datamart Commercial (commandes)
-- ============================================================

CREATE SCHEMA commercial;

-- Grain ligne de commande FluxPro (commandes/lignes_commande) --
-- commandes_clients volontairement hors périmètre, voir
-- modelisation_omega_bi.md §6.1.
CREATE TABLE commercial.fait_commande (
  commande_ligne_key  SERIAL PRIMARY KEY,
  client_key           INTEGER NOT NULL REFERENCES dimensions.dim_client(client_key),
  site_key             INTEGER NOT NULL REFERENCES dimensions.dim_site(site_key),
  produit_key          INTEGER NOT NULL REFERENCES dimensions.dim_produit(produit_key),
  date_key             INTEGER NOT NULL REFERENCES dimensions.dim_temps(date_key),
  commande_id          VARCHAR(30) NOT NULL,  -- dimension dégénérée, clé FluxPro
  quantite_commandee   INTEGER NOT NULL,
  poids_ligne          DECIMAL(8,2),
  statut_commande      VARCHAR(30) NOT NULL
);

-- ============================================================
-- Schéma "gouvernance" — gestion opérationnelle (C16)
-- ============================================================

CREATE SCHEMA gouvernance;

-- Journal des opérations de maintenance (chargements ETL, sauvegardes)
-- -- voir gestion_operationnelle_omega_bi.md §2. Aucune donnée métier
-- ou personnelle, uniquement des métadonnées d'exécution -- voir
-- registre_rgpd_entrepot.md.
CREATE TABLE gouvernance.journal_operations (
  id          SERIAL PRIMARY KEY,
  operation   VARCHAR(50) NOT NULL,   -- ex. load_warehouse, backup_complet
  demarre_le  TIMESTAMP NOT NULL,
  termine_le  TIMESTAMP,
  statut      VARCHAR(20) NOT NULL,   -- en_cours, succes ou echec
  details     TEXT,                   -- résumé libre (ex. comptes de lignes chargées)
  erreur      TEXT                    -- message d'erreur si statut = echec
);

CREATE VIEW gouvernance.v_dernieres_operations AS
SELECT
    operation, demarre_le, termine_le, statut,
    EXTRACT(EPOCH FROM (termine_le - demarre_le)) AS duree_secondes
FROM gouvernance.journal_operations
ORDER BY demarre_le DESC
LIMIT 20;

-- ============================================================
-- Accès (C16) — voir registre_rgpd_entrepot.md §4
-- ============================================================

-- Rôle bi_reader (créé par scripts/init_omega_bi_db.sh, avant la
-- migration Alembic qui exécute ces GRANT) : lecture seule sur
-- dimensions/exploitation/commercial, y compris les tables et vues
-- futures dans ces schémas (ALTER DEFAULT PRIVILEGES). "gouvernance"
-- est délibérément exclu : préoccupation d'exploitation technique, pas
-- un objet d'analyse métier -- vérifié en base (`\dp
-- gouvernance.journal_operations` ne montre aucun droit bi_reader).
GRANT USAGE ON SCHEMA dimensions, exploitation, commercial TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA dimensions, exploitation, commercial TO bi_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE datacore IN SCHEMA dimensions
  GRANT SELECT ON TABLES TO bi_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE datacore IN SCHEMA exploitation
  GRANT SELECT ON TABLES TO bi_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE datacore IN SCHEMA commercial
  GRANT SELECT ON TABLES TO bi_reader;

-- ============================================================
-- Mise à jour de ce fichier
-- ============================================================

-- Ce fichier n'est pas généré automatiquement à chaque migration -- à
-- régénérer/vérifier manuellement après toute migration Alembic
-- modifiant le schéma de l'entrepôt (nouvelle table, colonne, vue) :
--
--   docker compose -f infra/docker/docker-compose.yml exec -T db \
--     pg_dump -U datacore -d datacore_omega_bi --schema-only --no-owner --no-privileges
--
-- ...puis reporter les changements structurels ici, dans ce format
-- lisible et annoté (pas en collant le dump brut -- verbeux, sans les
-- commentaires de justification). Sert de point de comparaison en cas
-- de doute sur l'état réel du schéma.
