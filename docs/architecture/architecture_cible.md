# Étude technique d'architecture — Existant (AS IS) / Cible (TO BE)

**Compétence couverte : C3 — Concevoir un cadre technique d'exploitation des données**
**Épreuve associée : E2 (mise en situation professionnelle)**

Ce document fait suite à l'[étude de faisabilité](etude_faisabilite.md) (C1)
et à la [topographie des données](topographie_donnees.md) (C2). Il définit
l'architecture technique cible du programme DATA CORE : matrice des flux,
processus de mise en conformité RGPD, stratégie d'éco-responsabilité
(RGESN) et d'accessibilité (RGAA) des livrables.

---

## 1. Architecture existante (AS IS)

### 1.1 Constat

Reprise synthétique des constats de la [topographie des données](topographie_donnees.md)
et de l'[étude de faisabilité](etude_faisabilite.md#1-contexte) :

```
   Site Lyon                Site Lille               Site Marseille
 ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
 │  FluxPro    │          │  FluxPro    │          │  FluxPro    │
 │  (local)    │          │  (local)    │          │  (local)    │
 └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
        │ extractions            │ extractions            │ extractions
        │ Excel / SQL ad hoc     │ Excel / SQL ad hoc      │ Excel / SQL ad hoc
        ▼                        ▼                         ▼
 ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
 │  Fichiers   │          │  Fichiers   │          │  Fichiers   │
 │  partagés   │          │  partagés   │          │  partagés   │
 │  (par site) │          │  (par site) │          │  (par site) │
 └─────────────┘          └─────────────┘          └─────────────┘

        TransFlow (TMS) ─── consulté manuellement, pas de vue croisée FluxPro/TransFlow
        Fichiers clients (NordDrive, FreshMarket, MedioTex) ─── réceptionnés et ressaisis à la main
```

### 1.2 Limites identifiées

| Limite | Origine | Impact |
|---|---|---|
| Flux développés site par site, sans standardisation | Historique, absence de gouvernance data | Incidents non détectés en amont, indicateurs non comparables entre sites |
| Pas de vue consolidée FluxPro ↔ TransFlow | Deux systèmes cloisonnés, rapprochement manuel | Absence de suivi de bout en bout de l'expédition à la livraison |
| Fichiers clients hétérogènes ressaisis manuellement | Pas de traitement automatisé (C10) | Doublons, valeurs manquantes, temps perdu (chiffré en [C2 §3.3](topographie_donnees.md#33-fichiers-clients-bruts--formats-hétérogènes) : 55 à 68 % de doublons) |
| Absence de registre RGPD | Aucune gouvernance formalisée | Non-conformité, risque juridique jugé « zéro tolérance » par la sponsor |
| Aucun outil de catalogue ou de documentation partagée | Développements artisanaux non documentés | Dépendance aux personnes, perte de connaissance |
| Pas d'architecture prête pour la donnée massive (IoT) | Systèmes conçus pour la donnée transactionnelle uniquement | Incapacité à absorber la montée en charge annoncée (capteurs, géoloc, vidéo) |

---

## 2. Architecture cible (TO BE)

### 2.1 Principes directeurs

1. **Industrialisation** : remplacer les extractions manuelles par des
   scripts versionnés, testés et automatisables.
2. **Centralisation sans duplication inutile** : une base de staging
   unique en entrée de la chaîne, alimentant l'entrepôt et le data lake
   en aval (principe de sobriété, cf. §5).
3. **Sécurité et conformité by design** : authentification sur toutes les
   interfaces exposées, registre RGPD tenu dès la base de staging (et non
   ajouté a posteriori).
4. **Aucun outil imposé** : les choix technologiques ci-dessous sont des
   propositions raisonnées, cohérentes avec l'arborescence de référence du
   dépôt (`src/datacore/`), à ajuster selon les compétences de l'équipe.
5. **Accessibilité et éco-responsabilité intégrées dès le cadrage**, et non
   traitées comme un chantier annexe.

### 2.2 Vue en couches

```
┌───────────────────────────────────────────────────────────────────────┐
│ SOURCES                                                                │
│ FluxPro (CSV/SGBD) · TransFlow (API REST) · Portail transporteur (web) │
│ Fichiers clients (CSV hétérogènes) · Historique (CSV volumineux)       │
│ IoT batch (CSV/JSON) · IoT streaming (SSE)                             │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │
                    src/datacore/ingestion/
                    (connecteurs par type de source, C8)
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│ TRAITEMENT ET NETTOYAGE           src/datacore/processing/  (C9, C10)  │
│ dédoublonnage, homogénéisation dates/unités, contrôles qualité         │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│ STOCKAGE                          src/datacore/storage/                │
│                                                                         │
│  ┌─────────────────────┐   ETL   ┌────────────────────────────────┐  │
│  │ Base de staging      │ ──────► │ Entrepôt OMEGA BI (bloc 3)      │  │
│  │ (modèle MERISE, C11) │         │ étoile/flocon, datamarts (C13)  │  │
│  └──────────┬───────────┘         └────────────────────────────────┘  │
│             │                                                          │
│             │ IoT batch + streaming                                   │
│             ▼                                                          │
│  ┌──────────────────────────────────────────┐                        │
│  │ Data lake OMEGA LAKE (bloc 4)             │                        │
│  │ zones raw / staging / curated (C18)       │                        │
│  └────────────────────────────────────────────┘                      │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│ EXPOSITION                        src/datacore/api/  (C12)             │
│ Omega Data API (REST, OpenAPI, authentification/autorisation)          │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
        Équipes BI · Data science · Référents clients (accès restreint)

        Transverse : src/datacore/governance/ (RGPD, droits d'accès, C21)
                     src/datacore/config/ (paramétrage, secrets)
```

### 2.3 Choix technologiques proposés

| Brique | Proposition | Justification |
|---|---|---|
| Base de staging et entrepôt OMEGA BI | PostgreSQL (conteneurisé via `infra/docker/`, issue #7) | SGBD relationnel robuste, adapté à `data/schema.sql` et au modèle en étoile, open source (sobriété financière et RGESN) |
| Data lake OMEGA LAKE | Stockage objet compatible S3 (ex. MinIO en local) organisé en zones `raw/`, `staging/`, `curated/` | Standard de facto, portable, pas de dépendance à un fournisseur cloud propriétaire pour l'environnement pédagogique |
| Ingestion batch | Scripts Python versionnés (`src/datacore/ingestion/`) | Cohérent avec les compétences internes de l'équipe, aucun ETL propriétaire imposé |
| Ingestion streaming (capteurs) | Consommateur Python du flux SSE (`/api/stream/capteurs`) | Le pack technique n'impose pas de broker (Kafka, etc.) ; un consommateur simple suffit au périmètre pédagogique, une évolution vers un broker reste possible si le volume l'exige |
| API d'exposition | API REST documentée (OpenAPI), `src/datacore/api/` | Répond directement au livrable C12, réutilise les compétences déjà mobilisées sur l'API mock TransFlow |
| Orchestration | Scripts planifiés (cron / tâche planifiée) dans un premier temps | Proportionné au volume du programme ; un orchestrateur dédié (Airflow) reste une évolution possible, à documenter comme risque ouvert |
| Intégration continue | GitHub Actions (issue #8) | Lint et tests à chaque PR vers `dev`, cohérent avec la convention de branches du projet |
| Conteneurisation | `docker-compose` (issue #7) : service Postgres de staging + API mock | Reproductibilité de l'environnement de développement |

### 2.4 Correspondance avec l'arborescence du dépôt

| Module | Rôle | Compétences couvertes |
|---|---|---|
| `src/datacore/ingestion/` | Connecteurs par type de source (API, scraping, fichiers, SGBD, big data, IoT) | C8 |
| `src/datacore/processing/` | Nettoyage, agrégation, règles de transformation, ETL vers l'entrepôt | C9, C10, C15 |
| `src/datacore/storage/` | Modèles de données (staging, entrepôt en étoile, data lake), scripts de création | C11, C13, C14, C18 |
| `src/datacore/api/` | API REST de mise à disposition des données | C12 |
| `src/datacore/governance/` | Registre RGPD, droits d'accès par groupes, procédures de purge, catalogue | C16, C20, C21 |
| `src/datacore/config/` | Paramétrage, gestion des secrets (clé API, identifiants base) | Transverse (sécurité) |

### 2.5 Alternative écartée — Microsoft Fabric

Microsoft Fabric (OneLake, Lakehouse) a été envisagé puis écarté pour ce
programme, pour trois raisons :

- **Contrainte pédagogique** : le cahier des charges impose un
  fonctionnement local, sans compte cloud ni accès externe (« tout
  fonctionne en local sur votre machine ») — incompatible avec une
  plateforme SaaS.
- **Coût et dépendance fournisseur** : solution propriétaire payante
  au-delà d'un essai gratuit, contraire au principe de sobriété
  financière et à la stratégie RGESN retenue (§5).
- **Reproductibilité** : MinIO, conteneurisé en local et compatible API
  S3, garantit un environnement identique pour tout évaluateur relisant
  le projet, sans dépendance à un tenant Microsoft/Azure.

Ce choix n'exclut pas la pertinence de Microsoft Fabric dans un contexte
d'entreprise déjà intégré à l'écosystème Microsoft/Azure — cas de figure
hors périmètre de ce programme pédagogique.

---

## 3. Matrice des flux

| Flux | Source | Mode | Fréquence cible | Traitement | Destination | Sécurité | Module |
|---|---|---|---|---|---|---|---|
| F1 | FluxPro (`data/*.csv`) | Batch | Quotidien | Import direct via `schema.sql` | Base de staging | Accès local, aucune donnée réelle | `ingestion`, `storage` |
| F2 | TransFlow (`/api/*`) | Batch (extraction paginée) | Quotidien | Rapprochement par `tracking_number` | Base de staging | Clé API (`X-API-Key`), à externaliser en variable d'environnement | `ingestion` |
| F3 | Portail transporteur (scraping) | Batch | Quotidien | Parsing HTML | Base de staging | Aucune (source publique simulée) | `ingestion` |
| F4 | Fichiers clients (NordDrive, FreshMarket, MedioTex) | Batch | À réception (événementiel) | Dédoublonnage, homogénéisation dates/unités (C10) | Jeu de données brut unique | Aucune donnée réelle ; coordonnées clients à pseudonymiser si présentes | `ingestion`, `processing` |
| F5 | Historique (`omega_historique_expeditions.csv`) | Batch (chargement unique + rechargements) | Ponctuel / historique | Extraction SQL documentée (C9) | Base de staging / dataset analytique | Aucune | `ingestion` |
| F6 | Base de staging → OMEGA BI | Batch (ETL planifié) | Quotidien ou hebdomadaire | Passage table-relations → faits-dimensions, contrôles qualité (C15) | Entrepôt OMEGA BI | Accès restreint aux équipes BI | `processing`, `storage` |
| F7 | IoT batch (`data/iot/*`) | Batch | Quotidien | Ingestion vers zone raw, cataloguage | Data lake OMEGA LAKE | Anonymisation partielle sur la géolocalisation | `ingestion`, `storage`, `governance` |
| F8 | IoT streaming (`/api/stream/capteurs`) | Streaming (SSE) | Continu | Ingestion temps réel vers zone raw/curated | Data lake OMEGA LAKE | Clé API, conformité RGPD renforcée (géoloc chauffeurs) | `ingestion`, `governance` |
| F9 | Base de staging / OMEGA BI → consommateurs | API REST | À la demande | Authentification, autorisation par groupe | Équipes BI, data science, référents clients (lecture seule sur leur périmètre) | Authentification + autorisation (C12, C21) | `api`, `governance` |

---

## 4. Mise en conformité RGPD

### 4.1 Données à caractère personnel identifiées

| Donnée | Localisation | Sensibilité |
|---|---|---|
| Nom du chauffeur | TransFlow (`tournees.chauffeur`) | Identifiante |
| Géolocalisation de la flotte | IoT (`geoloc_flotte.csv`, flux streaming) | Sensible (associable à un chauffeur via `vehicule_id`) |
| Adresse de livraison | TransFlow (`livraisons.adresse_livraison`), portail transporteur | Identifiante (destinataire final) |
| Contacts clients | Éventuellement présents dans les fichiers clients bruts | Identifiante |

### 4.2 Registre des traitements (par brique)

| Brique | Traitement | Finalité | Base légale | Durée de conservation proposée | Mesure de protection |
|---|---|---|---|---|---|
| Base de staging | Import brut des données FluxPro/TransFlow/clients | Constitution du jeu de données consolidé | Intérêt légitime (exécution du contrat de prestation logistique) | Durée du traitement + purge après intégration à l'entrepôt | Accès restreint à l'équipe Pôle Data |
| Entrepôt OMEGA BI | Agrégation pour pilotage de la performance | Reporting décisionnel (taux de service, délais, coûts) | Intérêt légitime | Historisation nécessaire au pilotage (ex. 24 mois glissants) | Anonymisation des chauffeurs dans les vues agrégées, accès par groupe |
| Data lake OMEGA LAKE | Ingestion des données de géolocalisation et RFID | Suivi opérationnel temps réel, amélioration continue | Intérêt légitime, avec information des salariés concernés (chauffeurs) | Purge automatisée au-delà d'un horizon défini (ex. 90 jours pour la géolocalisation brute) | Pseudonymisation des identifiants véhicule/chauffeur, chiffrement au repos |

### 4.3 Droits d'accès par groupe

| Groupe | Périmètre d'accès | Justification |
|---|---|---|
| Data Engineers | Lecture/écriture sur staging, entrepôt, data lake | Réalisation et maintenance des pipelines |
| Data Analysts | Lecture sur entrepôt OMEGA BI (datamarts) | Reporting, sans besoin d'accéder aux données brutes |
| Référents clients externes (NordDrive, FreshMarket, MedioTex) | Lecture seule, restreinte à leur périmètre client, via l'API | Principe de minimisation des données, pas d'accès aux données des autres clients |
| Responsables d'entrepôt | Lecture sur les indicateurs de leur site | Besoin opérationnel exprimé en entretien (C1) |

### 4.4 Procédures de tri et de suppression

- Purge des données de géolocalisation brutes au-delà de la durée de
  conservation définie (§4.2), avec conservation d'indicateurs agrégés
  anonymisés à des fins de reporting long terme.
- Revue trimestrielle du registre des traitements par le Pôle Data.
- Application du principe de minimisation : les droits sont accordés par
  groupe fonctionnel, jamais par individu (cf. §4.3).

---

## 5. Stratégie d'éco-responsabilité (RGESN)

| Principe RGESN mobilisé | Application dans DATA CORE |
|---|---|
| Sobriété des données | Une base de staging unique en entrée, pas de duplication systématique des données brutes dans chaque brique aval ; l'entrepôt et le data lake ne stockent que ce qui répond à un besoin identifié |
| Sobriété des requêtes | Pagination systématique sur l'API TransFlow et sur l'Omega Data API (`page`, `per_page`), évitant les extractions complètes inutiles |
| Choix d'hébergement et d'outillage | Priorité aux solutions open source, conteneurisées localement (`docker-compose`), sans sur-dimensionnement de l'infrastructure par rapport au volume réel du programme |
| Cycle de vie des données | Procédures de purge définies dès la conception (§4.4), plutôt qu'une accumulation indéfinie |
| Choix des prestataires | Le prestataire SupervIT sera sélectionné/encadré en intégrant un critère d'éco-responsabilité dans le cahier des charges de sa mission (cf. feuille de route, C5) |
| Analyse du cycle de vie simplifiée | À produire pour les livrables numériques majeurs (API, tableau de bord) : évaluation qualitative de l'impact (stockage, calcul, transferts réseau) lors de leur mise en production |

---

## 6. Stratégie d'accessibilité numérique (RGAA)

- **Documentation** : les livrables Markdown/PDF du programme respectent
  une structure sémantique claire (titres hiérarchisés, tableaux avec
  en-têtes, texte alternatif pour les schémas), compatible avec les
  lecteurs d'écran — besoin concret remonté par les responsables
  d'entrepôt en entretien (site de Lille, cf.
  [étude de faisabilité §2.3](etude_faisabilite.md#23-entretien-avec-les-responsables-dentrepôt-lyon-lille-marseille)).
- **Interfaces** (tableau de bord, portail de restitution) : respect des
  recommandations RGAA (contrastes suffisants, navigation au clavier,
  alternatives textuelles), en s'appuyant sur les ressources de
  l'association Valentin Haüy et de Microsoft mentionnées au cahier des
  charges.
- **Anticipation dès l'avant-projet** : l'adaptation des postes de travail
  et interfaces pour les utilisateurs en situation de handicap est prise
  en compte dès la feuille de route (C5), et non traitée en fin de
  programme.

---

## 7. Synthèse des risques et recommandations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Non-conformité RGPD sur la géolocalisation des chauffeurs | Moyenne | Élevé | Registre des traitements dès la base de staging, purge automatisée (§4.4) |
| Sous-dimensionnement de l'architecture face à la montée en charge IoT | Moyenne | Moyen | Conception du data lake en zones dès le bloc 1 (§2.2), même si l'implémentation intervient au bloc 4 |
| Résistance au changement des responsables d'entrepôt | Moyenne | Moyen | Communication et implication dès le cadrage (C7), cohérent avec les retours d'entretien (C1) |
| Dépendance à une clé API statique non sécurisée pour TransFlow | Faible (contexte pédagogique) | Faible | Externalisation en variable d'environnement, à documenter comme limite du pack technique fourni |

Cette étude technique d'architecture alimente directement la feuille de
route du programme (C5) et servira de référence à la matrice des flux
détaillée lors de la réalisation du bloc 2 (C8-C12).
