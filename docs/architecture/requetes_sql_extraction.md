# Requêtes SQL d'extraction documentées — DATA CORE

**Compétence couverte : C9 — Développer des requêtes SQL d'extraction**
**Épreuve associée : E4 (mise en situation professionnelle)**

Ce document décrit les requêtes SQL versionnées dans
[`sql/extraction/`](../../sql/extraction/), qui extraient les commandes,
stocks et expéditions depuis la base FluxPro importée (C8, `data/schema.sql`)
et depuis l'historique volumineux chargé dans la base de staging (voir
§1 ci-dessous). Chaque requête est exécutable telle quelle contre la
base de staging PostgreSQL (`infra/docker/docker-compose.yml`).
Démonstration interactive avec sorties réelles :
[`notebooks/requetes_sql_extraction.ipynb`](../../notebooks/requetes_sql_extraction.ipynb).

---

## 1. Chargement de l'historique (« système big data »)

Choix technique : l'historique (25 000 lignes, `data/raw/historique/
omega_historique_expeditions.csv`) est chargé dans la **même base de
staging PostgreSQL** déjà en place (issue #7), dans une table dédiée
`historique_expeditions` (schéma :
[`sql/historique_schema.sql`](../../sql/historique_schema.sql)), plutôt
que dans un outil « big data » dédié (Spark, DuckDB...).

**Justification** : ce volume reste largement dans les capacités d'un
SGBD relationnel classique ; introduire un outil supplémentaire serait
disproportionné et contraire au principe de sobriété retenu (RGESN, voir
[architecture cible §5](architecture_cible.md#5-stratégie-déco-responsabilité-rgesn)).
Réutiliser la base de staging permet en plus des requêtes croisées avec
les données FluxPro.

```bash
./scripts/load_historique.sh
```

---

## 2. Requêtes documentées

### 2.1 Commandes par client et par période
[`sql/extraction/01_commandes_par_client_periode.sql`](../../sql/extraction/01_commandes_par_client_periode.sql)

Nombre de commandes et quantité totale par client et par mois (FluxPro :
`commandes` + `clients` + `lignes_commande`). Brique pour le futur
tableau de bord OMEGA BI (bloc 3, C13 — taux de service par
client/période).

```
   client    |          mois          | nb_commandes | quantite_totale
-------------+------------------------+--------------+-----------------
 FreshMarket | 2025-01-01 00:00:00+00 |           20 |             927
 FreshMarket | 2025-02-01 00:00:00+00 |           21 |            1190
 FreshMarket | 2025-03-01 00:00:00+00 |           27 |            1562
 ...
```

### 2.2 Stocks par entrepôt
[`sql/extraction/02_stocks_par_entrepot.sql`](../../sql/extraction/02_stocks_par_entrepot.sql)

Stocks actuels par entrepôt et produit, avec repère de rupture
(`quantite = 0`). Répond directement à l'irritant remonté par les
responsables d'entrepôt en entretien
([étude de faisabilité §2.3](etude_faisabilite.md#23-entretien-avec-les-responsables-dentrepôt-lyon-lille-marseille)) :
« les ruptures de stock ne sont détectées que lorsqu'une commande
échoue ». Aucune rupture n'est observée sur l'instantané actuel des
données (`SELECT count(*) FROM stocks WHERE quantite = 0` → 0), mais la
requête est prête à en détecter dès qu'une surviendra.

```
         entrepot         |    sku    |         libelle          | quantite |  date_maj  | en_rupture
--------------------------+-----------+--------------------------+----------+------------+------------
 Entrepot Omega Lille     | SKU-10001 | Plaquette de frein       |       16 | 2026-08-01 | f
 Entrepot Omega Lille     | SKU-10002 | Disque de frein          |      708 | 2026-07-28 | f
 ...
```

### 2.3 Expéditions en retard
[`sql/extraction/03_expeditions_en_retard.sql`](../../sql/extraction/03_expeditions_en_retard.sql)

Expéditions livrées après leur date prévue, avec le nombre de jours de
retard. Alimente directement l'indicateur « taux de service » attendu
par la Direction des Opérations
([étude de faisabilité §4](etude_faisabilite.md#4-étude-dopportunité)).

```
 tracking_number |     transporteur      |   client    | date_livraison_prevue | date_livraison_reelle | jours_retard
------------------+-----------------------+-------------+------------------------+------------------------+--------------
 OMG0001333      | EcoRoute              | NordDrive   | 2025-08-30            | 2025-09-02            |            3
 OMG0000527      | RapidFret             | MedioTex    | 2025-07-30            | 2025-08-02            |            3
 ...
```

### 2.4 Délais et coûts par client (historique)
[`sql/extraction/04_historique_delais_couts_par_client.sql`](../../sql/extraction/04_historique_delais_couts_par_client.sql)

Délai moyen de livraison, coût de transport moyen et taux de retard par
client, sur l'historique volumineux (2022-2026).

```
   client    | nb_expeditions | delai_moyen_jours | cout_moyen_eur | taux_retard_pct
-------------+----------------+-------------------+-----------------+-----------------
 FreshMarket |           8297 |               2.2 |           48.26 |            11.2
 NordDrive   |           8291 |               2.2 |           48.46 |            11.0
 MedioTex    |           8412 |               2.2 |           48.43 |            10.6
```

### 2.5 Évolution annuelle du délai (historique)
[`sql/extraction/05_evolution_delai_historique_par_annee.sql`](../../sql/extraction/05_evolution_delai_historique_par_annee.sql)

Évolution annuelle du délai moyen de livraison par client — illustre une
analyse de tendance sur la source « système big data », hors périmètre
opérationnel FluxPro (qui ne couvre que les commandes en cours).

```
   client    | annee | nb_expeditions | delai_moyen_jours
-------------+-------+----------------+-------------------
 FreshMarket |  2022 |           1784 |               2.2
 FreshMarket |  2023 |           1799 |               2.2
 FreshMarket |  2024 |           1865 |               2.2
 FreshMarket |  2025 |           1823 |               2.2
 FreshMarket |  2026 |           1026 |               2.1
 ...
```

---

## 3. Point de vigilance pour C11/C13

Les requêtes 2.1-2.3 utilisent `clients.nom` (FluxPro) ; les requêtes
2.4-2.5 utilisent `historique_expeditions.client` (libellé texte libre).
Un rapprochement explicite (`clients.nom` ↔ `historique_expeditions.client`)
sera nécessaire lors de la modélisation de la base de travail consolidée
(C11) et de l'entrepôt de données (bloc 3, C13) — déjà anticipé dans la
[topographie des données §3.4](topographie_donnees.md#34-historique-volumineux--système-big-data-).
