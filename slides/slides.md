---
theme: seriph
title: DATA CORE — Soutenance
titleTemplate: '%s'
info: |
  ## DATA CORE
  Soutenance orale — Certification Data Engineer (RNCP37638)
  Omega Logistics — Alexandre Laugier
class: text-center
highlighter: shiki
lineNumbers: true
drawings:
  persist: false
transition: fade
mdc: true
---

# DATA CORE

Refonte de l'infrastructure data d'Omega Logistics

<div class="pt-8 opacity-70">
Alexandre Laugier — Certification Data Engineer (RNCP37638)
</div>

<!--
Trame calibrée sur `docs/architecture/sequencement_m6.md` §1.2-2
(minutage hypothèse de travail, à confirmer avec le formateur).
Durée totale visée : ~90-100 minutes, 4 blocs + jalons transverses + Q&R.
-->

---
layout: default
---

# Sommaire — ~90-100 minutes

| Section | Durée visée |
|---|---|
| Contexte Omega Logistics / DATA CORE | ~5' |
| Bloc 1 — Cadrage (C1-C7) | ~30-35' |
| Bloc 2 — Collecte & Stockage (C8-C12), avec démonstration | ~15' |
| Bloc 3 — Entrepôt OMEGA BI (C13-C17), avec temps d'échange dédié | ~15-20' |
| Bloc 4 — Data Lake OMEGA LAKE (C18-C21) | ~10' |
| M4 (Grafana) + synthèse transverse + conclusion | ~10-15' |
| Questions & échanges avec le jury | ~10' |

<!--
Minutage calibré sur le déroulé E1-E7 de la certification (Bloc1=E1+E2+E3,
Bloc2=E4, Bloc3=E5+E6, Bloc4=E7) -- pas un livrable écrit séparé par
épreuve, décision actée le 22/10/2026 (sequencement_m6.md §1.2).
-->

---
layout: default
---

# Contexte — Omega Logistics

Prestataire logistique (3PL), 3 sites : **Lyon, Lille, Marseille**

<div class="grid grid-cols-3 gap-4 mt-8">
<div class="p-4 rounded border border-gray-400/30">
<b>NordDrive</b><br/>Pièces automobiles, flux tendus
</div>
<div class="p-4 rounded border border-gray-400/30">
<b>FreshMarket</b><br/>Grande distribution alimentaire, température & traçabilité
</div>
<div class="p-4 rounded border border-gray-400/30">
<b>MedioTex</b><br/>Textile, forte saisonnalité
</div>
</div>

<div class="mt-8">
Deux systèmes historiques, développés site par site, sans standardisation :

- **FluxPro** (WMS) — commandes, stocks, expéditions
- **TransFlow** (TMS) — tournées de la flotte
</div>

<!--
Dispersion → erreurs/incidents récurrents, pas de vision consolidée pour
la Direction des Opérations. Commanditaire : Éléonore RAKOTO (DOps),
sponsor Pôle Data : Karim BELAÏD.
-->

---
layout: default
---

# Objectifs SMART du programme

5 objectifs (`etude_faisabilite.md` §7), séquencés par une analyse RICE en 4 blocs de compétences :

1. Centraliser FluxPro, TransFlow, fichiers clients dans une base unique
2. Exposer la donnée consolidée via une **API documentée**
3. Mettre à disposition un **tableau de bord** (taux de service, délais, coûts)
4. **Zéro** traitement de données personnelles non répertorié (registre RGPD)
5. Concevoir une **architecture de data lake** pour le flux IoT

<!--
Les 5 objectifs sont atteints à la clôture (chapitre 7 du rapport) --
mais pas tous du premier coup : l'objectif 3 a nécessité un détour
(vues SQL/notebook insuffisantes → jalon M4 Grafana), à dire honnêtement.
-->

---
layout: section
---

# Bloc 1 — Cadrage
## C1-C7 — ~30-35'

<!-- Clos le 25/08/2026 (M0). Calibré sur E1 (5') + E2 (20') + E3 (10'). -->

---
layout: default
---

# C1 — Analyser l'expression d'un besoin

`docs/architecture/etude_faisabilite.md`

- Entretiens parties prenantes (commanditaire, sponsor, responsables d'entrepôt)
- Analyse d'opportunité et de faisabilité
- Priorisation **RICE** des blocs de compétences
- Objectifs **SMART**

<div class="mt-6 text-sm opacity-70">
L'analyse RICE arbitre directement le séquencement retenu : collecte avant
entrepôt, entrepôt avant data lake.
</div>

---
layout: image-right
backgroundSize: contain
image: /images/topographie_donnees_cartographie_sources.png
---

# C2 — Cartographier les données

`docs/architecture/topographie_donnees.md`

7 sources explorées **directement dans le code** (`data/raw/`, `api-mock/`),
pas depuis une description théorique :

- FluxPro (WMS), TransFlow (TMS)
- Portail transporteur (scraping)
- Fichiers clients hétérogènes
- Historique volumineux
- 2 flux IoT (anticipant le Bloc 4)

---
layout: default
---

# C3 — Concevoir un cadre technique d'exploitation

`docs/architecture/architecture_cible.md`

- Cible AS IS / TO BE, matrice des flux
- Registre RGPD préliminaire par brique technique
- Stratégie RGESN (éco-conception) et RGAA (accessibilité)

<div class="mt-8 p-4 rounded bg-blue-500/10 border border-blue-500/30">
<b>Décision structurante :</b> MinIO plutôt que Microsoft Fabric pour le
futur data lake — fonctionnement local sans compte cloud, coût,
reproductibilité pour un évaluateur tiers. Confirmée par la veille
technique du même jour.
</div>

---
layout: default
---

# C4 — Veille technique et réglementaire

`docs/architecture/veille_technique_reglementaire.md`

Journal hebdomadaire sur **3 semaines**, deux axes :

- **Technique** — DataOps / ETL
- **Réglementaire** — RGPD / RGAA

Chaque entrée reliée à une **décision réelle** du programme — pas un exercice isolé.

---
layout: image-right
backgroundSize: contain
image: /images/feuille_de_route_gantt.png
---

# C5 — Planifier la réalisation

`docs/architecture/feuille_de_route.md`

- 4 phases ↔ 4 blocs de compétences
- Composition d'équipe
- Budget prévisionnel : **180 000 €**
- Gantt / PERT en **Mermaid** (texte versionné)
- Suivi : GitHub Projects

---
layout: default
---

# C6 — Superviser la réalisation

`docs/architecture/supervision_projet.md`

- Rituels d'équipe : point hebdomadaire, comité de suivi mensuel
- Tableau de suivi budgétaire actualisé à chaque jalon

<div class="mt-8 p-4 rounded bg-green-500/10 border border-green-500/30">
Budget du périmètre initial (180 000 €) consommé intégralement sur
l'ensemble du programme (M0 à M4) — <b>aucun dépassement</b>.
</div>

---
layout: two-cols
---

# Workflow Git

`main` protégée (releases uniquement) · `dev` intégration continue ·
`feat-<n>-<slug>` par issue

- Toute PR cible `dev`, jamais `main` directement
- CI en 3 étapes séquentielles : `ruff` → `mypy` → `pytest`
- GitHub Projects, 6 statuts (Backlog → … → Terminé)

::right::

<img src="/images/supervision_projet_cycle_de_vie_1_developpement.png" class="rounded">

<!--
Le mécanisme d'automatisation "linked PR" a été essayé puis abandonné le
25/08/2026 : trop rigide pour les PR de release qui ferment plusieurs
issues à la fois. 176 tests au 21/10/2026.
-->

---
layout: image-right
backgroundSize: contain
image: /images/supervision_projet_cycle_de_vie_2_integration.png
---

# Workflow Git (suite)

Revue et intégration, jusqu'à la release

- À la clôture du dernier issue d'un jalon : compte rendu +
  release vers `main` dans la même PR
- Puis fermeture du milestone GitHub correspondant

---
layout: default
---

# C7 — Communiquer tout au long du projet

`docs/architecture/communication_lancement.md`

- Plan de communication aux parties prenantes à chaque étape clé
- Attention portée à l'accessibilité des documents partagés (RGAA)

---
layout: fact
---

# 4 / 7

Compétences couvertes par le suivi GitHub initial du Bloc 1

<!--
Écart constaté et traité AVANT clôture (pas découvert par le jury) :
le suivi initial (issues #1-#8) ne couvrait que 4 des 7 compétences --
gap identifié à la première rédaction du compte rendu M0, comblé par
3 issues supplémentaires (C4, C6, C7). Réflexe resté constant sur tout
le programme (cf. réexamen du périmètre C20, Bloc 4).
-->

---
layout: section
---

# Bloc 2 — Collecte & Stockage
## C8-C12 — ~15' (avec démonstration)

<!-- Clos le 27/08/2026 (M1). Calibré sur E4 (15'). -->

---
layout: default
---

# Séquencement retenu

`docs/architecture/sequencement_bloc2.md`

<div class="text-2xl text-center mt-8 font-bold">
C8 → C10 → C9 → C11 → C12
</div>

<div class="mt-8 p-4 rounded bg-blue-500/10 border border-blue-500/30">
Diffère volontairement de l'ordre naturel du cahier des charges (qui
aurait suggéré de modéliser avant d'agréger) — le grain réel des
doublons n'a été découvert qu'en traitant concrètement les données,
pas en les modélisant par anticipation.
</div>

---
layout: image-right
backgroundSize: contain
image: /images/diagrammes_techniques_ingestion_c8.png
---

# C8 — Automatiser l'extraction

5 connecteurs, 31 tests :

- API REST (TransFlow)
- Scraping du portail transporteur
- Requêtes SQL directes (FluxPro)
- Fichiers clients hétérogènes
- Historique volumineux

<div class="mt-4 text-sm opacity-70">→ Démo live à ce point (voir issue #98)</div>

---
layout: default
---

# C9 — Requêtes SQL d'extraction

`docs/architecture/requetes_sql_extraction.md`

5 requêtes documentées avec leurs résultats réels.

<div class="mt-8 p-4 rounded bg-blue-500/10 border border-blue-500/30">
Historique chargé dans la base de staging PostgreSQL existante, pas dans
un outil « big data » séparé : au volume réel (25 000 lignes), disproportionné —
choix de sobriété numérique (RGESN), pas de principe.
</div>

---
layout: default
---

# C10 — Règles d'agrégation : le bon grain compte

```python
grain_counts = Counter((r[key], r[prod_key]) for r in rows)
true_dups = {k: v for k, v in grain_counts.items() if v > 1}
```

<div class="grid grid-cols-2 gap-4 mt-6">
<div class="p-4 rounded bg-red-500/10 border border-red-500/30">
<b>Grain « commande » seul</b><br/>
55 à 68 % de doublons — chiffre trompeur (mesure le nombre moyen de
produits par commande)
</div>
<div class="p-4 rounded bg-green-500/10 border border-green-500/30">
<b>Grain (commande, produit)</b><br/>
13 à 17 % selon le client — taux réel, retenu et implémenté
(<code>deduplicate()</code>)
</div>
</div>

---
layout: image-right
backgroundSize: contain
image: /images/modelisation_merise_mcd.png
---

# C11 — Créer une base de données

Méthode MERISE, versionnée via Alembic

- 2 violations de formes normales trouvées **empiriquement**, corrigées
- Clé de rapprochement `tracking_number` (livraisons ↔ expéditions),
  **sans FK formelle** — systèmes sources distincts

---
layout: image-right
backgroundSize: contain
image: /images/diagrammes_techniques_api_sequence_autorisation.png
---

# C12 — Partager le jeu de données

API **Omega Data** (FastAPI → OpenAPI auto-générée)

Authentification par clé, autorisation par rôle.

<div class="mt-4 p-4 rounded bg-blue-500/10 border border-blue-500/30">
Un référent client externe n'est pas <i>rejeté</i> s'il demande un autre
client — il est <i>silencieusement ramené</i> à son propre périmètre.
Vérifié en conditions réelles.
</div>

---
layout: default
---

# Point ouvert → transmis au Bloc 3

`clients.nom` (FluxPro) ↔ `historique_expeditions.client` (texte libre)

**Rapprochement non garanti par une contrainte formelle** à ce stade —
signalé explicitement pour traitement lors de la modélisation de
l'entrepôt.

---
layout: section
---

# Bloc 3 — Entrepôt OMEGA BI
## C13-C17 — ~15-20' (avec temps d'échange)

<!-- Clos le 21/09/2026 (M2). Calibré sur E5 (10') + E6 (5-10', échange). -->

---
layout: default
---

# Séquencement retenu

`docs/architecture/sequencement_bloc3.md`

<div class="text-2xl text-center mt-8 font-bold">
C13 → C14 → C15 → C17 → C16
</div>

<div class="mt-8 p-4 rounded bg-blue-500/10 border border-blue-500/30">
Inversion volontaire de C16/C17 par rapport au Gantt initial : la purge
RGPD de C16 dépend du schéma historisé que C17 doit d'abord créer.
</div>

---
layout: image-right
backgroundSize: contain
image: /images/modelisation_omega_bi_mcd.png
---

# C13 — Modéliser l'entrepôt

Approche bottom-up Kimball : **2 datamarts, 3 faits, 6 dimensions conformées**

<div class="mt-4 text-sm">
<b>Pourquoi pas de <code>Fait_Livraison</code> séparée ?</b><br/>
100 % des 1100 expéditions FluxPro ont exactement une livraison TransFlow
correspondante (1:1 vérifié empiriquement) — scinder aurait imposé une
jointure fait-à-fait à chaque requête.
</div>

---
layout: image-right
backgroundSize: contain
image: /images/creation_entrepot_omega_bi_schemas.png
---

# C14 — Créer l'entrepôt

PostgreSQL, instance partagée avec le staging (sobriété RGESN)

5 schémas : `dimensions`, `exploitation`, `commercial`, `gouvernance`, `monitoring`

<div class="mt-4 text-sm opacity-70">
Cycle upgrade/downgrade vérifié contre une base réelle — un bug latent
Alembic (<code>include_schemas=True</code>) n'a été révélé qu'à la
seconde migration.
</div>

---
layout: default
---

# C15 — Développer des pipelines de données

Pipeline ETL staging → entrepôt

- Contrôles qualité réels : mise en **quarantaine** des lignes non rapprochées
- Cohérence vérifiée par **double calcul indépendant** : ETL vs API (C12)
  — deux chemins distincts, même résultat

---
layout: default
---

# C16 — Gestion opérationnelle

`docs/architecture/gestion_operationnelle_omega_bi.md`

- Sauvegardes planifiées (partielle/complète) — 7 des 8 tables reconstructibles depuis le staging
- Journalisation réelle (`gouvernance`), connexion dédiée (survit à un `ROLLBACK`)
- Registre RGPD : audit automatisé répétable, aucune donnée personnelle trouvée

<div class="mt-6 p-4 rounded bg-blue-500/10 border border-blue-500/30">
Périmètre étendu après clôture initiale : vues SQL + notebook jugés
insuffisants comme preuve de restitution → jalon transverse M4.
</div>

---
layout: default
---

# C17 — Variation de dimension (SCD2)

```python
if current and current[1] == r["nom"] and current[2] == r["secteur"]:
    mapping[r["id"]] = current[0]
    continue
if current is not None:
    cur.execute("""UPDATE dimensions.dim_client
        SET valid_to = %(today)s, is_current = false
        WHERE client_key = %(client_key)s""", {...})
# ... puis INSERT d'une nouvelle ligne
```

`Dim_Client` historisée en **SCD2** : un changement de `nom`/`secteur` ferme
la version courante et en ouvre une nouvelle — jamais d'écrasement.

---
layout: center
class: text-center
---

# Temps d'échange — Bloc 3

Questions du jury sur la modélisation / l'entrepôt

<div class="opacity-70 mt-4">(calibré sur E6, échange questions-réponses — pas une présentation continue)</div>

---
layout: section
---

# Bloc 4 — Data Lake OMEGA LAKE
## C18-C21 — ~10'

<!-- Clos le 23/09/2026 (M3). Calibré sur E7 (10'). -->

---
layout: image-right
backgroundSize: contain
image: /images/architecture_omega_lake_trois_couches.png
---

# C18 — Architecture du data lake

**Schema-on-read**, pas schema-on-write (staging/entrepôt)

Flux IoT en ingestion directe, **jamais** par la base de staging
relationnelle — la zone `curated/` se joint à la lecture aux dimensions
conformées de l'entrepôt.

---
layout: image-right
backgroundSize: contain
image: /images/architecture_omega_lake_zones.png
---

# C18 — Zones raw / staging / curated

`docs/architecture/architecture_omega_lake.md`

Clés naturelles de jointure vérifiées dans les données, jamais supposées.

---
layout: default
---

# C19 — Intégrer l'infrastructure

MinIO (S3) + **DuckDB** (jointures) + **boto3** (copie fidèle de `raw/`)

<div class="mt-4 p-4 rounded bg-blue-500/10 border border-blue-500/30">
DuckDB peut reformater silencieusement un CSV/JSON en le réécrivant —
incompatible avec la garantie « octet pour octet » de <code>raw/</code>
(vérifiée par somme de contrôle SHA-256). <code>boto3</code> transfère
des octets sans les interpréter.
</div>

**Flux SSE** fenêtré par intervalle de 5 minutes, vérifié par **coupure
brutale réelle** (`kill -9` puis redémarrage) : aucune collision, aucune
donnée corrompue.

---
layout: default
---

# C20 — Catalogue de données

Généré par **introspection réelle** (`boto3` + `DESCRIBE` DuckDB), jamais
maintenu à la main — même principe que l'audit RGPD automatisé de C16 :
un catalogue généré ne peut pas devenir silencieusement obsolète.

<div class="mt-4 text-sm opacity-70">
Périmètre élargi avant tout code : construire le contenu réel de
<code>staging/</code>/<code>curated/</code>, pas seulement cataloguer
<code>raw/</code> comme le texte initial de l'issue le suggérait.
</div>

---
layout: default
---

# C21 — Gouvernance : le parcours de la pseudonymisation

```python
def pseudonyme(vehicule_id: str, cle: str | None = LAKE_PSEUDONYM_KEY) -> str:
    cle = verifier_cle_configuree(cle)
    return hmac.new(cle.encode(), vehicule_id.encode(), hashlib.sha256).hexdigest()[:16]
```

1. Risque identifié dès C18 (recoupement géoloc ↔ chauffeur)
2. Première analyse incomplète — écartée, puis **réintroduite** après relecture externe
3. HMAC implémenté — hash simple = recalculable par force brute sur 15 véhicules
4. Repli codé en dur trouvé en **2ᵉ relecture** → garde-fou `verifier_cle_configuree()`
5. Risque résiduel assumé (stabilité de la clé entre exécutions) — documenté, pas masqué

---
layout: section
---

# M4 — Restitution BI (Grafana)
## + synthèse transverse + conclusion — ~10-15'

---
layout: default
---

# Pourquoi M4 ? Un écart réel, pas un choix éditorial

Référentiel C16 (act. 6) : « tableau de bord » exigé pour les indicateurs de service<br/>
Référentiel C20 : monitorage des « conditions matérielles et applicatives » + alerte sur rupture

<div class="mt-6 p-4 rounded bg-red-500/10 border border-red-500/30">
Vues SQL + notebook (C16) et catalogue par introspection (C20), bien que
réels et vérifiés, <b>ne constituent pas</b> un tableau de bord ni un
monitorage actif au sens de ces critères — détecté après la clôture de
M2/M3.
</div>

Grafana, auto-hébergé — seule forme satisfaisant littéralement les deux critères.
Décidé avant Power BI (cloud) ou Databricks (workspace dédié).

---
layout: image-right
backgroundSize: contain
image: /images/gestion_operationnelle_omega_bi_dashboard_grafana.png
---

# C16bis — Restitution OMEGA BI

Dashboard Grafana connecté en lecture seule (`bi_reader`)

<div class="mt-4 p-4 rounded bg-orange-500/10 border border-orange-500/30">
3 bugs réels trouvés <b>uniquement en testant depuis un vrai navigateur</b>
— invisibles depuis les vérifications par appel direct à l'API Grafana,
qui passaient toutes.
</div>

<div class="mt-2 text-sm font-bold">
Leçon : une vérification par API seule ne prouve jamais qu'un rendu
côté client fonctionne pour l'utilisateur final.
</div>

---
layout: default
---

# C20bis — Monitorage du data lake

Relevé de santé infrastructure (MinIO, capacité) + règle d'alerte Grafana réelle

Grafana → service interne authentifié → `smtplib` → MailHog

<div class="mt-4 p-4 rounded bg-green-500/10 border border-green-500/30">
Testé de bout en bout, deux fois : coupure réelle de MinIO → alerte
active en ~30s → e-mail reçu dans MailHog. Remise en service → alerte résolue.
</div>

---
layout: default
---

# Limite assumée : granularité réelle du monitorage

| Flux | Suivi |
|---|---|
| **SSE capteurs** (`flux_sse_capteurs`) | Fraîcheur/volumétrie oui — débit, latence, déconnexion **non** |
| **Scraping portail transporteur** | **Aucun** suivi persisté — `print()` console uniquement |

<div class="mt-6 text-sm opacity-70">
Le monitorage (<code>monitoring</code>, C20bis) a été construit
spécifiquement pour C20 (data lake, Bloc 4) — le Bloc 2 n'a jamais eu
d'équivalent. Écart identifié en relisant le code, pas découvert par
le jury — documenté chapitre 6 du rapport, issue #104 (backlog).
</div>

---
layout: default
---

# Synthèse transverse — Budget cumulé

| Phase | Montant | Statut |
|---|---|---|
| Phase 1 — Cadrage (M0) | 25 000 € | Consommé |
| Phase 2 — Collecte & Stockage (M1) | 45 000 € | Consommé |
| Phase 3 — Entrepôt OMEGA BI (M2) | 55 000 € | Consommé |
| Phase 4 — Data Lake OMEGA LAKE (M3) | 55 000 € | Consommé |
| **Total** | **180 000 €** | **Aucun dépassement** |

<div class="mt-4 text-sm opacity-70">
Jalons transverses (M4, M5, M6) : staffing interne uniquement, outils
open source auto-hébergés — jamais de ligne budgétaire propre.
</div>

---
layout: default
---

# Synthèse transverse — Qualité : évolution des tests

| Jalon | Fonctions de test | Évolution |
|---|---|---|
| M0 — Cadrage & Setup | 13 | — |
| M1 — Collecte & Stockage | 67 | ×5,2 |
| M2 — Entrepôt OMEGA BI | 96 | +43 % |
| M3 — Data Lake OMEGA LAKE | 143 | +49 % |
| M4 — Restitution BI | 174 (176 cas pytest) | +22 % |

<div class="mt-4 text-sm opacity-70">
Croissance non linéaire avec le volume de code : les blocs 2 et 3
ajoutent proportionnellement plus de tests, cohérent avec une suite qui
couvre systématiquement les cas limites.
</div>

---
layout: default
---

# Gouvernance : un fil transverse RGPD-RGESN-RGAA

- **RGPD** — la pseudonymisation (C21) : risque identifié → analyse
  incomplète écartée → réintroduite après relecture → faille (repli
  codé en dur) trouvée en 2ᵉ relecture → risque résiduel assumé
- **RGESN** — critère invoqué à chaque choix d'infrastructure
  (pas de « big data » séparé, pas d'orchestrateur, outils auto-hébergés)
- **RGAA** — accessibilité appliquée en continu aux livrables
  Markdown/PDF, pas vérifiée une seule fois en fin de programme

<div class="mt-6 text-sm font-bold">
Motif qui se répète : chaque étape déclenchée par une relecture externe
trouvant un défaut dans l'étape précédente — jamais un audit générique.
</div>

---
layout: default
---

# Conclusion — Objectifs SMART

Les 5 objectifs sont atteints à la clôture (M0 à M4) — **mais pas tous du
premier coup** :

1. Centraliser FluxPro/TransFlow/fichiers clients ✅
2. API REST documentée (Omega Data) ✅
3. Tableau de bord ✅ — en **deux temps** (vues SQL/notebook → Grafana M4)
4. Zéro traitement RGPD non répertorié ✅
5. Architecture data lake pour le flux IoT ✅

---
layout: default
---

# Limites connues

- **Aucune interaction réelle avec un système tiers externe** — toutes
  les sources sont simulées par `api-mock` (limite structurelle du pack pédagogique)
- Rapprochement `clients.nom` ↔ `historique_expeditions.client` non garanti par contrainte formelle
- Aucun ordonnanceur actif (sauvegardes, purge RGPD) — scripts documentés, exécution manuelle/cron
- Stabilité de la clé de pseudonymisation entre exécutions non surveillée
- Prestataire SupervIT jamais mobilisé — écart budgétaire/organisationnel assumé
- Observabilité partielle par choix (pas de Loki/ELK, pas de tracing distribué)

---
layout: default
---

# Apprentissages

- **Décider avant de coder** — un document de séquencement par bloc,
  écrit et daté avant la première ligne de code
- **Vérifier empiriquement plutôt que supposer** — grain réel des
  doublons, cardinalité 1:1 vérifiée, citations du référentiel relues au mot près
- **La relecture externe comme détecteur d'angles morts** — la
  restitution BI (M4) et la faille de repli codé en dur ont toutes deux
  été trouvées par un regard extérieur après une première analyse jugée suffisante

<div class="mt-6 p-4 rounded bg-blue-500/10 border border-blue-500/30">
Programme mené avec l'assistance d'outils d'IA sous supervision humaine
constante — chaque décision structurante arbitrée et validée par le
Data Engineer, jamais déléguée. Historique Git public disponible.
</div>

---
layout: center
class: text-center
---

# Questions & échanges avec le jury

<div class="opacity-70 mt-4">~10' — ouvert à tous les blocs</div>

---
layout: end
---

# Merci

<div class="opacity-70">
Dépôt public : github.com/alaugier/datacore
</div>
