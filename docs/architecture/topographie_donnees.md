# Topographie des données — DATA CORE

**Compétence couverte : C2 — Cartographier les données disponibles**
**Épreuve associée : E2 (mise en situation professionnelle)**

Ce document fait suite à l'[étude de faisabilité](etude_faisabilite.md) (C1)
et couvre la sémantique métier (glossaire), les modèles de données des
systèmes existants (FluxPro, TransFlow, fichiers clients), la cartographie
des traitements et flux, ainsi que les modalités d'accès. Il s'appuie sur
l'exploration effective du pack technique `datacore-dataset` (copié en
local dans `data/raw/`, jamais versionné — voir `.gitignore`) et sur l'API
mock TransFlow (`api-mock/app.py`).

---

## 1. Glossaire métier

| Terme | Définition dans le contexte Omega Logistics |
|---|---|
| **3PL** (Third-Party Logistics) | Prestataire logistique externalisé gérant entreposage, préparation de commandes et transport pour le compte de tiers (les clients d'Omega Logistics). |
| **WMS** (Warehouse Management System) | Système de gestion d'entrepôt. Chez Omega Logistics : **FluxPro**, qui pilote commandes, stocks, produits et expéditions. |
| **TMS** (Transport Management System) | Système de gestion du transport. Chez Omega Logistics : **TransFlow**, qui organise tournées et livraisons de la flotte. |
| **Entrepôt** | Site d'exploitation d'Omega Logistics. Trois sites : Lyon (`OMG-LYO`), Lille (`OMG-LIL`), Marseille (`OMG-MAR`). |
| **Client** | Donneur d'ordre d'Omega Logistics. Trois clients fictifs : NordDrive (pièces auto), FreshMarket (grande distribution alimentaire), MedioTex (textile). |
| **Commande** | Demande d'expédition de produits passée par un client pour un entrepôt donné, composée d'une ou plusieurs lignes de commande. |
| **Ligne de commande** | Association d'un produit et d'une quantité au sein d'une commande. |
| **Expédition** | Envoi physique résultant d'une commande, confié à un transporteur, identifié par un numéro de suivi (`tracking_number`). |
| **Stock** | Quantité disponible d'un produit dans un entrepôt à une date de mise à jour donnée. |
| **SKU** (Stock Keeping Unit) | Référence unique d'un produit dans le référentiel FluxPro. |
| **Température dirigée** | Produit nécessitant une conservation en chaîne du froid (concerne notamment FreshMarket). |
| **Tournée** | Ensemble de livraisons affectées à un chauffeur et un véhicule, pour une date donnée, organisé par TransFlow. |
| **Livraison** | Remise d'un colis (une expédition) à une adresse, rattachée à une tournée, avec un statut et des horaires estimé/réel. |
| **Transporteur** | Société assurant le transport physique des expéditions (ex. RapidFret). Distinct d'Omega Logistics, dont TransFlow orchestre les tournées. |
| **Portail transporteur** | Interface web fictive de suivi de colis exposée par un transporteur, à parcourir/scraper (pas d'API disponible côté transporteur). |
| **Taux de service** | Indicateur clé de performance : proportion de livraisons effectuées dans les délais/conditions convenus. |
| **SLA** (Service Level Agreement) | Accord de niveau de service définissant la qualité de prestation attendue. |
| **RFID** (Radio Frequency Identification) | Technologie d'étiquetage/scan sans contact utilisée pour tracer les palettes en entrepôt. |
| **IoT** (Internet of Things) | Capteurs connectés en entrepôt (température, comptage caméra) et sur la flotte (géolocalisation), anticipant le bloc 4 (data lake). |
| **Staging** | Base de données de travail intermédiaire, cible de la collecte du bloc 2, alimentant ensuite l'entrepôt de données (bloc 3). |

---

## 2. Cartographie des sources de données

Le référentiel de certification (compétence C8) attend la couverture de
cinq types de sources ; le pack technique fourni les couvre toutes, plus
une sixième catégorie (données IoT) anticipant le bloc 4 :

| Type de source | Système / origine | Emplacement local | Volumétrie constatée |
|---|---|---|---|
| Base de données (SGBD) | FluxPro (WMS) | `data/raw/*.csv` + `data/raw/schema.sql` | 7 tables, de 3 à 4 186 lignes (détail §3.1) |
| Service web (API REST) | TransFlow (TMS, mock) | `api-mock/app.py` (`http://127.0.0.1:5050/api/*`) | 3 transporteurs, 139 tournées, 1 100 livraisons |
| Page web à scraper | Portail transporteur (mock) | `api-mock/app.py` (`/portail-transporteur/*`) | 1 100 fiches colis (une par livraison) |
| Fichiers de données | Flux clients bruts | `data/raw/clients_fichiers/*.csv` | 3 fichiers, ~1 300 à 1 500 lignes chacun, formats hétérogènes |
| Système big data | Historique d'expéditions | `data/raw/historique/omega_historique_expeditions.csv` | 25 000 lignes, 2022-2026 |
| IoT batch (hors périmètre bloc 2, anticipé bloc 4) | Capteurs entrepôts + flotte | `data/raw/iot/*.csv`, `rfid_scans.json` | ~2 200 à 3 000 lignes/fichier |
| IoT temps réel (anticipé bloc 4) | Flux capteurs simulé | `api-mock/app.py` (`/api/stream/capteurs`, SSE) | flux continu, non borné |

Toutes les routes `/api/*` de TransFlow exigent l'en-tête
`X-API-Key: datacore-training-2026` (authentification par clé statique,
suffisante pour un usage pédagogique mais à proscrire en environnement de
production réel — point à traiter dans l'étude technique d'architecture,
C3).

---

## 3. Modèles de données

### 3.1 FluxPro (WMS) — base relationnelle

Sept tables liées par clés étrangères (`data/raw/schema.sql`). Modèle
conceptuel simplifié :

```
Client (1) ───< Produit
Client (1) ───< Commande >─── (1) Entrepot
Commande (1) ───< LigneCommande >─── (1) Produit
Commande (1) ───< Expedition
Entrepot (1) ───< Stock >─── (1) Produit
```

| Table | Clé primaire | Clés étrangères | Attributs métier | Lignes |
|---|---|---|---|---|
| `entrepots` | `id` | — | `code`, `nom`, `ville`, `capacite_palettes` | 3 |
| `clients` | `id` | — | `code`, `nom`, `secteur` | 3 |
| `produits` | `id` | `client_id → clients.id` | `sku`, `libelle`, `categorie`, `poids_kg`, `temperature_dirigee` | 30 |
| `commandes` | `id` | `client_id`, `entrepot_id` | `date_commande`, `statut` | 1 400 |
| `lignes_commande` | `id` | `commande_id`, `produit_id` | `quantite` | 4 186 |
| `expeditions` | `id` | `commande_id` | `tracking_number`, `transporteur`, `date_expedition`, `date_livraison_prevue`, `date_livraison_reelle`, `statut` | 1 100 |
| `stocks` | `id` | `entrepot_id`, `produit_id` | `quantite`, `date_maj` | 90 |

**Remarques pour la modélisation MERISE (C11)** : le champ `transporteur`
de `expeditions` est une chaîne libre non reliée à la table TransFlow
(source distincte, cf. §3.2) — un rapprochement (jointure applicative sur
le `tracking_number`) sera nécessaire lors de l'agrégation. `statut` est
répété sur `commandes` et `expeditions` avec des valeurs métier propres à
chaque étape du cycle de vie (ex. `Livree`, `En cours`, `Retardee`).

### 3.2 TransFlow (TMS) — API REST + portail à scraper

**API REST** (`api-mock/app.py`, préfixe `/api`) :

| Endpoint | Description | Filtres / pagination |
|---|---|---|
| `GET /api/health` | Disponibilité (sans authentification) | — |
| `GET /api/transporteurs` | Liste des transporteurs | — |
| `GET /api/tournees` | Tournées | `date`, `transporteur_id`, `page`, `per_page` |
| `GET /api/tournees/<id>` | Détail d'une tournée | — |
| `GET /api/tournees/<id>/livraisons` | Livraisons d'une tournée | — |
| `GET /api/livraisons` | Livraisons | `statut`, `page`, `per_page` |
| `GET /api/livraisons/<id>` | Détail d'une livraison | — |
| `GET /api/stream/capteurs` | Flux capteurs temps réel (SSE) — anticipation bloc 4 | — |

Modèle de données exposé :

| Entité | Clé | Attributs | Relie vers |
|---|---|---|---|
| `Transporteur` | `id` | `nom`, `contact` | — |
| `Tournee` | `id` | `transporteur_id`, `date`, `vehicule_id`, `chauffeur` | `Transporteur` |
| `Livraison` | `id` | `tournee_id`, `tracking_number`, `adresse_livraison`, `statut`, `heure_estimee`, `heure_reelle` | `Tournee`, et par `tracking_number` → `Expedition` (FluxPro) |

**Portail transporteur (page web à scraper)**, routes HTML sans API
sous-jacente côté transporteur — usage volontaire pour couvrir la source
« page web » du référentiel :

- `GET /portail-transporteur/colis` — liste HTML d'un échantillon de colis
  (liens vers le détail).
- `GET /portail-transporteur/colis/<tracking_number>` — fiche HTML d'un
  colis : statut, adresse de livraison, heure estimée/réelle, tournée.

Le rapprochement `Livraison.tracking_number ↔ Expedition.tracking_number`
est la clé de jointure entre les univers FluxPro et TransFlow.

### 3.3 Fichiers clients bruts — formats hétérogènes

Trois fichiers de commandes envoyés par les clients, volontairement
disparates (`data/raw/clients_fichiers/`), à harmoniser lors de
l'agrégation (compétence C10) :

| Client | Fichier | Délimiteur | Colonnes | Format de date observé | Particularité |
|---|---|---|---|---|---|
| NordDrive | `norddrive_commandes.csv` | `;` | `ref_commande, date_cde, reference_piece, designation, qte, poids_unitaire_g, entrepot` | 3 formats mêlés : `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD` | poids en **grammes** (FluxPro utilise des kg) |
| FreshMarket | `freshmarket_commandes.csv` | `,` | `id_commande_client, date_reception, code_article, libelle_produit, quantite_commandee, chaine_froid_requise, site_livraison` | 3 formats mêlés : `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD` | booléen métier `OUI`/`NON` (chaîne du froid) |
| MedioTex | `mediotex_commandes.csv` | `,` | `numero_cde, date, sku, description, quantite, entrepot_destination` | 3 formats mêlés : `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD` | format le plus proche du modèle FluxPro (`sku` déjà nommé ainsi) |

**Qualité des données constatée.** Un identifiant de commande répété dans
un fichier correspond très majoritairement à une commande **multi-produits
légitime** (plusieurs lignes, un produit par ligne — comme
`lignes_commande` dans FluxPro), pas à un doublon : ce n'est donc pas le
bon grain de mesure. Le grain pertinent est **(commande, produit)** :

| Fichier | Lignes | Couples (commande, produit) uniques | Vrais doublons (couple répété) | Cellules vides détectées |
|---|---|---|---|---|
| `norddrive_commandes.csv` | 1 479 | 1 263 | 186 | 29 (colonne `qte`) |
| `freshmarket_commandes.csv` | 1 288 | 1 110 | 161 | 27 (colonne `quantite_commandee`) |
| `mediotex_commandes.csv` | 1 496 | 1 260 | 218 | 0 |

Ces vrais doublons correspondent le plus souvent à des lignes en conflit
(même commande, même produit, **quantité différente** et/ou date reformatée)
plutôt qu'à des répétitions exactes — cohérent avec les irritants remontés
par Karim BELAÏD en entretien (voir
[étude de faisabilité §2.1](etude_faisabilite.md#21-entretien-avec-karim-belaïd--responsable-du-pôle-data))
et justifient la compétence C10 (règles d'agrégation et de nettoyage,
voir [`src/datacore/processing/clients_cleaning.py`](../../src/datacore/processing/clients_cleaning.py)) :
dédoublonnage au grain (commande, produit) avec résolution des conflits,
unification des formats de date, conversion des unités (grammes → kg),
normalisation des booléens métier, et suppression des lignes à quantité
manquante.

> Correction du 26/08/2026 : la première version de cette section mesurait
> le taux de doublons au grain (commande) seul, ce qui surestimait
> fortement le phénomène (55 à 68 %) en confondant commandes
> multi-produits et doublons réels. Voir le commit associé pour
> l'historique.

### 3.4 Historique volumineux (« système big data »)

`data/raw/historique/omega_historique_expeditions.csv` — 25 000 lignes,
période 2022-2026, une ligne par expédition agrégée :

| Colonne | Type | Description |
|---|---|---|
| `id` | entier | Identifiant de la ligne |
| `client` | texte | Nom du client (NordDrive, FreshMarket, MedioTex) |
| `entrepot` | texte | Ville d'entrepôt (nom complet, pas le code FluxPro) |
| `categorie_produit` | texte | Catégorie du produit expédié |
| `date_expedition` | date | Date d'expédition |
| `poids_kg` | décimal | Poids de l'expédition |
| `delai_livraison_jours` | entier | Délai constaté |
| `cout_transport_eur` | décimal | Coût de transport |
| `statut` | texte | Statut final (`Livree`, `Retardee`, ...) |

Point d'attention pour la modélisation : les identifiants (`client`,
`entrepot`) sont ici des libellés texte et non des clés étrangères vers
FluxPro — une correspondance devra être établie (ex. `Lyon` ↔ `OMG-LYO`)
lors de l'intégration dans l'entrepôt de données (bloc 3).

### 3.5 Données IoT (anticipation du bloc 4 — data lake OMEGA LAKE)

Hors périmètre de collecte du bloc 2, mais déjà présentes dans le pack
technique et à prendre en compte dès la cartographie pour anticiper
l'architecture cible (C3) :

| Fichier / flux | Format | Colonnes | Volumétrie |
|---|---|---|---|
| `iot/capteurs_temperature.csv` | CSV | `timestamp, entrepot, zone, temperature_c, alerte` | 2 592 lignes |
| `iot/geoloc_flotte.csv` | CSV | `timestamp, vehicule_id, lat, lon, vitesse_kmh` | 2 160 lignes |
| `iot/camera_comptage.csv` | CSV | `timestamp, entrepot, zone, nb_passages, sens` | 432 lignes |
| `iot/rfid_scans.json` | JSON (liste d'objets) | `scan_id, timestamp, palette_id, entrepot, zone, produit_sku` | 3 000 entrées |
| `/api/stream/capteurs` | SSE (flux continu) | `timestamp, entrepot, zone, temperature_c, vehicule_id, lat, lon` | non borné (1 évènement / 2 s) |

Ces cinq flux illustrent les trois dimensions du big data (volumétrie,
variété — CSV/JSON/streaming —, vitesse) qui justifient, en toute logique
métier, le recours à un data lake plutôt qu'à un entrepôt décisionnel
classique pour ce périmètre.

---

## 4. Cartographie des traitements et flux

Vue d'ensemble des flux de données identifiés, de la source au futur
usage (les blocs 2 à 4 sont indiqués à titre de repère, la réalisation
proprement dite fait l'objet des issues suivantes) :

| # | Source | Traitement attendu | Destination | Bloc concerné |
|---|---|---|---|---|
| 1 | FluxPro (`data/*.csv`) | Import direct via `schema.sql` | Base de staging | Bloc 2 (C8, C9, C11) |
| 2 | TransFlow (API `/api/*`) | Extraction paginée, authentifiée par clé API | Base de staging | Bloc 2 (C8) |
| 3 | Portail transporteur (scraping HTML) | Parsing des pages colis | Base de staging | Bloc 2 (C8) |
| 4 | Fichiers clients (3 formats hétérogènes) | Nettoyage, dédoublonnage, homogénéisation dates/unités | Jeu de données brut unique | Bloc 2 (C10) |
| 5 | Historique volumineux (25 000 lignes) | Chargement dans l'outil « big data » retenu, requêtes d'extraction | Base de staging / dataset analytique | Bloc 2 (C9) |
| 6 | Base de staging consolidée | Exposition sécurisée | API REST « Omega Data API » (OpenAPI) | Bloc 2 (C12) |
| 7 | Base de staging | Modélisation en étoile/flocon, pipelines ETL | Entrepôt OMEGA BI (faits/dimensions) | Bloc 3 (C13-C15) |
| 8 | IoT batch (`data/iot/*`) + flux temps réel (`/api/stream/capteurs`) | Ingestion batch et streaming, catalogage | Data lake OMEGA LAKE (zones raw/staging/curated) | Bloc 4 (C18-C20) |

Cette chaîne confirme le séquencement déjà retenu dans l'
[analyse RICE de l'étude de faisabilité](etude_faisabilite.md#6-analyse-rice) :
la centralisation FluxPro/clients et la mise en conformité RGPD priment,
l'entrepôt décisionnel vient ensuite, le data lake en dernier.

---

## 5. Modalités d'accès

| Source | Mode d'accès | Authentification | Contrainte d'usage |
|---|---|---|---|
| FluxPro (`data/*.csv`, `schema.sql`) | Fichiers plats, import SQL | Aucune (fichiers locaux) | Ne jamais versionner les données brutes (`data/raw/` exclu du dépôt Git, voir `.gitignore`) |
| TransFlow (`/api/*`) | API REST HTTP (JSON) | En-tête `X-API-Key: datacore-training-2026` | Pagination obligatoire (`page`, `per_page`, max 200/page) ; clé statique à ne jamais committer en clair dans un script (variable d'environnement) |
| Portail transporteur (`/portail-transporteur/*`) | Pages HTML | Aucune | Respect d'un rythme de requêtes raisonnable (pas de throttling implémenté côté mock, mais bonne pratique à documenter) |
| Fichiers clients (`clients_fichiers/*.csv`) | Fichiers plats | Aucune | Formats hétérogènes par client — traitement dédié par source (C10) |
| Historique (`historique/*.csv`) | Fichier plat volumineux | Aucune | À charger dans un outil adapté au volume (25 000 lignes ne nécessite pas d'infrastructure distribuée, mais la démarche doit rester généralisable) |
| IoT batch (`iot/*.csv`, `rfid_scans.json`) | Fichiers plats CSV/JSON | Aucune | Anticiper le passage à l'échelle pour le bloc 4 |
| IoT streaming (`/api/stream/capteurs`) | Server-Sent Events | `X-API-Key` | Connexion longue durée ; nécessite un consommateur dédié (pas de rejeu possible, flux non historisé côté source) |

**Point de vigilance RGPD** (à détailler dans l'étude technique
d'architecture, C3) : les champs `chauffeur` (TransFlow), `adresse_livraison`
(TransFlow/portail) et les coordonnées clients potentiellement présentes
dans les fichiers clients constituent des données à caractère personnel,
à recenser dans le registre des traitements dès la base de staging.

---

## 6. Synthèse

| Dimension | Constat |
|---|---|
| Complétude des sources | Les cinq types de sources attendus par le référentiel (C8) sont couverts, plus les flux IoT anticipant le bloc 4 |
| Qualité | Bonne sur FluxPro et TransFlow (données structurées et cohérentes) ; dégradée sur les fichiers clients (13 à 17 % de doublons au grain commande/produit, 3 formats de date mêlés, quelques valeurs manquantes) |
| Volumétrie | Modeste sur FluxPro/TransFlow (dizaines à milliers de lignes) ; plus significative sur l'historique (25 000 lignes) et les flux IoT (jusqu'à ~3 000 lignes par fichier, flux temps réel non borné) |
| Interopérabilité | Rapprochement nécessaire entre référentiels : `tracking_number` (FluxPro ↔ TransFlow), codes vs libellés d'entrepôt (FluxPro ↔ historique), `sku` hétérogènes selon les fichiers clients |
| Sécurité d'accès | Authentification minimale (clé API statique) sur TransFlow, aucune sur les autres sources locales — à renforcer dans l'architecture cible (C3) et l'API de mise à disposition (C12) |

Cette topographie alimente directement l'étude technique d'architecture
AS IS / TO BE (C3) et la feuille de route du programme (C5).
