# Pipelines ETL vers l'entrepôt OMEGA BI

**Compétence couverte : C15 — Développer des pipelines de données**
**Épreuve associée : E5**

Ce document décrit le pipeline ETL qui peuple l'entrepôt OMEGA BI
(schéma créé en C14) depuis la base de travail (staging, C11), en
appliquant les règles de transformation conçues en C13
(`docs/architecture/modelisation_omega_bi.md`).

---

## 1. Architecture du pipeline

[`src/datacore/storage/warehouse/load_warehouse.py`](../../src/datacore/storage/warehouse/load_warehouse.py) :
une fonction par table de dimension/fait, orchestrées par `main()`.
Deux bases Postgres distinctes (staging et entrepôt) : aucune jointure
SQL croisée possible, toute transformation se fait en Python entre
l'extraction (lecture staging) et le chargement (écriture entrepôt).

```bash
alembic -c alembic_omega_bi.ini upgrade head    # si pas déjà fait (C14)
python3 -m datacore.storage.warehouse.load_dim_temps  # si pas déjà fait (C14)
python3 -m datacore.storage.warehouse.load_warehouse
```

**Rechargement complet, pas incrémental** : chaque exécution vide
d'abord les 8 tables qu'elle alimente (`TRUNCATE ... CASCADE`, tout sauf
`dimensions.dim_temps` — chargée séparément par C14) puis recharge tout
depuis staging. Choix délibéré : cohérent avec le rythme batch
quotidien/hebdomadaire prévu (`architecture_cible.md`, flux F6) et avec
l'absence d'historisation avant C17 (SCD2 sur `Dim_Client`) — un
rechargement complet est plus simple à raisonner et à tester qu'une
logique d'upsert incrémentale tant qu'aucune dimension ne conserve
d'historique. **Idempotent par construction** (pas via `ON CONFLICT`) :
rejouer le pipeline produit exactement le même état, vérifié pour de
vrai en le lançant deux fois de suite (voir §4).

---

## 2. Règles de transformation

| Table entrepôt | Source(s) staging | Règle |
|---|---|---|
| `dimensions.dim_client` | `clients` | Copie directe, clé de substitution générée |
| `dimensions.dim_site` | `entrepots` | Copie directe |
| `dimensions.dim_categorie` | `produits.categorie` (valeurs distinctes) | Dimension à grain réduit, conforme aux deux sources de `Fait_Expedition` |
| `dimensions.dim_produit` | `produits` | Copie + FK vers `dim_categorie` |
| `dimensions.dim_transporteur` | `transporteurs` | `nom` uniquement (`contact` exclu, RGPD *by design*) + membre « Inconnu » |
| `exploitation.fait_stock` | `stocks` | Grain (entrepôt, produit, date) direct |
| `commercial.fait_commande` | `commandes` + `lignes_commande` | Grain ligne ; `poids_ligne = quantite × produits.poids_kg` |
| `exploitation.fait_expedition` | `expeditions` + `commandes` + `lignes_commande` + `produits` (FluxPro/TransFlow) **et** `historique_expeditions` (Historique) | Voir §2.1 et §2.2 |

### 2.1 `Fait_Expedition`, partie FluxPro/TransFlow

- `poids_kg` : `expeditions` ne porte pas de poids directement — calculé
  en sommant `lignes_commande.quantite × produits.poids_kg` pour la
  commande liée (sous-requête corrélée).
- `categorie_key` : dérivée du client, pas du produit — `expeditions`
  n'a pas de lien direct vers un produit précis. S'appuie sur le fait
  (vérifié empiriquement en C13,
  `notebooks/exploration_donnees_omega_bi.ipynb` §2) qu'un client n'a
  des produits que dans une seule catégorie ; `client_categorie_keys()`
  revérifie cette hypothèse à l'exécution et lève une erreur explicite
  si elle s'avérait fausse sur un futur jeu de données, plutôt que de
  choisir une catégorie arbitrairement.
- `transporteur_key` : `expeditions.transporteur` est un texte libre
  (`"RapidFret"`), rapproché de `dim_transporteur.nom` par jointure
  textuelle exacte — mécanisme déjà documenté et vérifié en C13
  (`modelisation_omega_bi.md` §5.1).
- `livre_a_lheure` : `date_livraison_reelle <= date_livraison_prevue` —
  **même définition** que `datacore.api.repository.taux_service_par_client`
  (C12), pour rester cohérent avec le KPI déjà exposé par l'API.
  `None` si l'expédition n'est pas encore livrée
  (`date_livraison_reelle IS NULL`).
- `cout_transport_eur` : toujours `NULL` — absent de FluxPro/TransFlow
  (limite déjà documentée en C13).

### 2.2 `Fait_Expedition`, partie Historique — contrôle qualité par quarantaine

`client`, `entrepot` et `categorie_produit` sont du texte libre côté
historique, sans contrainte garantissant leur cohérence avec les
référentiels FluxPro (voir `modelisation_omega_bi.md` §5.1/§8). Plutôt
que d'insérer une ligne avec une clé de dimension incorrecte, ou de
rejeter le chargement entier au premier écart, chaque ligne est
vérifiée individuellement : si `client`, `entrepot` **ou**
`categorie_produit` ne correspond à aucune valeur connue, la ligne est
**mise en quarantaine** (comptée, non insérée) et le chargement continue.
Le nombre de lignes en quarantaine est reporté dans le résumé
d'exécution — sur ce jeu de données, **0 ligne en quarantaine** (les 3
clients/entrepôts/catégories de l'historique correspondent exactement
aux référentiels connus, vérifié en C13).

`livre_a_lheure` reste `NULL` pour ces lignes : l'historique ne fournit
qu'un délai constaté (`delai_livraison_jours`), pas de date de livraison
prévue à comparer — calculer un « à l'heure » à partir du seul champ
`statut` (`Retardee`/`Incident`) confondrait deux notions différentes
(un flag de retard textuel vs. une comparaison de dates) ; non fait
plutôt que d'inventer une règle non vérifiée.

---

## 3. Contrôles qualité

- **Unicité** : `dimensions.dim_categorie.libelle` et le grain de
  `exploitation.fait_stock` (`site_key`, `produit_key`, `date_key`) sont
  contraints en base (C14, `UNIQUE`) — une violation lève une erreur
  Postgres explicite plutôt que d'insérer un doublon silencieux.
- **Doublons entre exécutions** : évités par construction (`TRUNCATE` +
  rechargement complet, §1), pas par une logique `ON CONFLICT` à
  maintenir.
- **Rapprochement textuel de l'historique** : quarantaine ligne par
  ligne plutôt que rejet en bloc ou clé fausse (§2.2).
- **Hypothèse « un client = une catégorie »** : revérifiée à chaque
  exécution (`client_categorie_keys`), `ValueError` explicite si mise en
  défaut plutôt qu'un choix arbitraire silencieux.
- **Formats de sortie** : `date_key` toujours dérivée via `_date_key()`
  (garantit le format `YYYYMMDD` entier attendu par `dimensions.dim_temps`) ;
  types alignés sur le schéma SQLAlchemy de C14 (`models.py`).

---

## 4. Procédure de test

**Tests unitaires** (`tests/unit/test_load_warehouse.py`, 12 tests) :
connexions/curseurs factices, sur le même principe que
`test_load_staging.py`/`test_api_repository.py` — construction des
mappings de clés, calcul de `poids_ligne`, dérivation de
`livre_a_lheure`/`delai_livraison_jours` (livré vs. en cours), logique
de quarantaine, `ValueError` sur l'hypothèse client/catégorie mise en
défaut.

**Test de bout en bout réel** (Docker Compose), effectué lors de la
création de ce livrable — chaîne complète C7→C8→C9→C10→C11 (staging)
puis C14→C15 (entrepôt) :

```
dim_client: 3, dim_site: 3, dim_categorie: 3, dim_produit: 30, dim_transporteur: 3 + 1 (Inconnu)
fait_stock: 90, fait_commande: 4186, fait_expedition: 1100 (FluxPro/TransFlow) + 25000 (Historique)
lignes historique mises en quarantaine: 0
```

Vérifications supplémentaires effectuées :
- **Idempotence** : pipeline relancé deux fois de suite, comptes
  strictement identiques au second passage.
- **Cohérence avec l'API C12** : le taux de service par client calculé
  depuis `Fait_Expedition` (`livre_a_lheure`) donne exactement les mêmes
  chiffres que `taux_service_par_client` (staging direct) — ex.
  FreshMarket 245 expéditions, 90,6 %, identique aux deux calculs.
- **Cohérence des agrégats** : somme de `quantite_commandee` et
  `poids_ligne` sur `Fait_Commande` identique à la somme calculée
  directement sur `lignes_commande`/`produits` en staging (86 140 unités,
  290 548,75 kg).
- **Jointures de dimension** : `Fait_Stock` rejoint correctement
  `Dim_Site`/`Dim_Produit`/`Dim_Temps` (échantillon vérifié ligne à
  ligne contre `stocks.csv`).

---

## 5. Références

- [`modelisation_omega_bi.md`](modelisation_omega_bi.md) — modélisation
  étoile/flocon implémentée ici (C13).
- [`creation_entrepot_omega_bi.md`](creation_entrepot_omega_bi.md) —
  création physique de l'entrepôt (C14), prérequis de ce pipeline.
- [`api_omega_data.md`](api_omega_data.md) — définition de
  `taux_service_par_client`, réutilisée pour `livre_a_lheure` (§2.1).
