-- Schéma de la table historique_expeditions, alimentée depuis
-- data/raw/historique/omega_historique_expeditions.csv (C9).
--
-- Choix technique : réutilisation de la base de staging PostgreSQL déjà
-- en place (issue #7) plutôt qu'un outil « big data » dédié (Spark,
-- DuckDB...) — le volume (25 000 lignes) reste largement dans les
-- capacités d'un SGBD relationnel classique, et introduire un outil
-- supplémentaire serait disproportionné et contraire au principe de
-- sobriété retenu (RGESN, voir docs/architecture/architecture_cible.md
-- §5). Cela permet aussi des requêtes croisées avec les données FluxPro
-- (voir sql/extraction/).

CREATE TABLE IF NOT EXISTS historique_expeditions (
  id                      INTEGER PRIMARY KEY,
  client                  VARCHAR(50)   NOT NULL,
  entrepot                VARCHAR(50)   NOT NULL,
  categorie_produit       VARCHAR(50),
  date_expedition         DATE,
  poids_kg                DECIMAL(8,2),
  delai_livraison_jours   INTEGER,
  cout_transport_eur      DECIMAL(8,2),
  statut                  VARCHAR(30)
);
