---
theme: seriph
title: DATA CORE — Soutenance
titleTemplate: '%s'
info: |
  ## DATA CORE
  Soutenance orale — Certification Data Engineer (RNCP37638)
  Omega Logistics — Alexandre Laugier
class: text-center text-white
layout: cover
background: '#0b2545'
highlighter: shiki
lineNumbers: true
drawings:
  persist: false
transition: fade
mdc: true
---

<img src="/illustrations/logistics.svg" class="abs-tr mt-12 mr-8 h-56" style="filter: brightness(0) invert(1); opacity: 0.18;">

<div class="absolute left-0 right-0 top-0 h-2" style="background: linear-gradient(90deg, #1c7ed6, #22b8cf, #1c7ed6);"></div>

# DATA CORE

Refonte de l'infrastructure data d'Omega Logistics

<div class="pt-8 opacity-80">
Alexandre Laugier — Certification Data Engineer (RNCP37638)
</div>

<div class="abs-bl ml-8 mb-8 bg-white rounded-lg px-4 py-2 inline-block">
<img src="/images/simplon_logo.png" class="h-6">
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
| [Contexte Omega Logistics / DATA CORE](3) | ~5' |
| [Bloc 1 — Cadrage (C1-C7)](5) | ~30-35' |
| [Bloc 2 — Collecte & Stockage (C8-C12), avec démonstration](15) | ~15' |
| [Bloc 3 — Entrepôt OMEGA BI (C13-C17), avec temps d'échange dédié](24) | ~15-20' |
| [Bloc 4 — Data Lake OMEGA LAKE (C18-C21)](32) | ~10' |
| [M4 (Grafana) + synthèse transverse + conclusion](39) | ~10-15' |
| [Questions & échanges avec le jury](51) | ~10' |

<!--
Minutage calibré sur le déroulé E1-E7 de la certification (Bloc1=E1+E2+E3,
Bloc2=E4, Bloc3=E5+E6, Bloc4=E7) -- pas un livrable écrit séparé par
épreuve, décision actée le 22/10/2026 (sequencement_m6.md §1.2).
-->

---
layout: image-right
backgroundSize: contain
image: /illustrations/logistics.svg
---

# Contexte — Omega Logistics

<div class="flex items-center gap-2">
<div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style="background:#1c7ed6"><img src="/icons/building-warehouse.svg" class="w-4 h-4"></div>
<p class="text-sm">Prestataire logistique (3PL), 3 sites :</p>
</div>

<div class="grid grid-cols-3 gap-3 mt-2">
<div class="p-2 rounded border border-gray-400/30 text-center">
<img src="/icons/building-warehouse-blue.svg" class="h-8 mx-auto">
<div class="text-sm font-bold mt-1">Lyon</div>
</div>
<div class="p-2 rounded border border-gray-400/30 text-center">
<img src="/icons/building-warehouse-blue.svg" class="h-8 mx-auto">
<div class="text-sm font-bold mt-1">Lille</div>
</div>
<div class="p-2 rounded border border-gray-400/30 text-center">
<img src="/icons/building-warehouse-blue.svg" class="h-8 mx-auto">
<div class="text-sm font-bold mt-1">Marseille</div>
</div>
</div>

<div class="grid grid-cols-1 gap-2 mt-4">
<div class="flex items-center gap-3 p-2 rounded border border-gray-400/30">
<div class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style="background:#1c7ed6"><img src="/icons/engine.svg" class="w-5 h-5"></div>
<div class="text-sm"><b>NordDrive</b> — pièces automobiles, flux tendus</div>
</div>
<div class="flex items-center gap-3 p-2 rounded border border-gray-400/30">
<div class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style="background:#2f9e44"><img src="/icons/shopping-cart.svg" class="w-5 h-5"></div>
<div class="text-sm"><b>FreshMarket</b> — grande distribution alimentaire, température & traçabilité</div>
</div>
<div class="flex items-center gap-3 p-2 rounded border border-gray-400/30">
<div class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style="background:#e8590c"><img src="/icons/shirt.svg" class="w-5 h-5"></div>
<div class="text-sm"><b>MedioTex</b> — textile, forte saisonnalité</div>
</div>
</div>

<div class="mt-4 text-sm">
Deux systèmes historiques, développés site par site, sans standardisation :
<b>FluxPro</b> (WMS — commandes, stocks, expéditions) et <b>TransFlow</b>
(TMS — tournées de la flotte).
</div>

<!--
Dispersion → erreurs/incidents récurrents, pas de vision consolidée pour
la Direction des Opérations. Commanditaire : Éléonore RAKOTO (DOps),
sponsor Pôle Data : Karim BELAÏD.
-->

---
layout: default
---

# Objectifs SMART<sup>1</sup> du programme

5 objectifs (`etude_faisabilite.md` §7), séquencés par une analyse RICE<sup>2</sup> en 4 blocs de compétences :

1. Centraliser FluxPro, TransFlow, fichiers clients dans une base unique
2. Exposer la donnée consolidée via une **API documentée**
3. Mettre à disposition un **tableau de bord** (taux de service, délais, coûts)
4. **Zéro** traitement de données personnelles non répertorié (registre RGPD)
5. Concevoir une **architecture de data lake** pour le flux IoT

<div class="grid grid-cols-[1fr_auto_1fr_auto_1fr] gap-3 items-center mt-6 text-sm text-center">
<div class="p-3 rounded-lg bg-blue-500/10 border-2 border-blue-500/30">
<img src="/icons/target.svg" class="h-7 mx-auto mb-1">
5 objectifs SMART
</div>
<div class="text-xl opacity-40">→</div>
<div class="p-3 rounded-lg bg-green-500/10 border-2 border-green-500/30">
<img src="/icons/sort-ascending-2.svg" class="h-7 mx-auto mb-1">
Score RICE par chantier
</div>
<div class="text-xl opacity-40">→</div>
<div class="p-3 rounded-lg bg-orange-500/10 border-2 border-orange-500/30">
<img src="/icons/stack-2.svg" class="h-7 mx-auto mb-1">
4 blocs de compétences séquencés
</div>
</div>

<div class="mt-6 text-xs opacity-60 border-t border-gray-400/20 pt-2">
<sup>1</sup> SMART : Spécifique, Mesurable, Acceptable/Ambitieux, Réaliste, Temporellement défini &nbsp;·&nbsp;
<sup>2</sup> RICE : Reach, Impact, Confidence, Effort
</div>

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

<img src="/illustrations/route-planning.svg" class="mx-auto mt-6 h-40">

<!-- Clos le 25/08/2026 (M0). Calibré sur E1 (5') + E2 (20') + E3 (10'). -->

---
layout: default
---

# C1 — Analyser l'expression d'un besoin

<div class="grid grid-cols-[55%_45%] gap-6 items-center mt-2">
<div>
<p class="text-sm"><code>docs/architecture/etude_faisabilite.md</code></p>
<ul class="text-sm mt-2 space-y-1">
<li>Entretiens parties prenantes (commanditaire, sponsor, responsables d'entrepôt)</li>
<li>Analyse d'opportunité et de faisabilité</li>
<li>Priorisation <b>RICE</b> des blocs de compétences</li>
<li>Objectifs <b>SMART</b></li>
</ul>
<div class="mt-3 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
L'analyse RICE arbitre directement le séquencement retenu : collecte avant
entrepôt, entrepôt avant data lake.
</div>
</div>
<img src="/illustrations/brainstorming.svg" class="w-full">
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
- 2 flux IoT (anticipant le Bloc 4) :

<div class="flex items-center gap-4 mt-1 ml-4">
<div class="flex items-center gap-1 text-xs"><img src="/icons/thermometer.svg" class="h-5">capteur température</div>
<div class="flex items-center gap-1 text-xs"><img src="/icons/gps.svg" class="h-5">géolocalisation</div>
<div class="flex items-center gap-1 text-xs"><img src="/icons/camera.svg" class="h-5">caméra comptage</div>
</div>

---
layout: default
---

# C3 — Concevoir un cadre technique d'exploitation

`docs/architecture/architecture_cible.md`

- Cible AS IS / TO BE, matrice des flux
- Registre RGPD préliminaire par brique technique
- Stratégie RGESN (éco-conception) et RGAA (accessibilité)

<div class="mt-8 p-4 rounded bg-blue-500/10 border border-blue-500/30 flex items-center gap-4">
<img src="/logos/minio.svg" class="h-10 flex-shrink-0">
<div><b>Décision structurante :</b> MinIO plutôt que Microsoft Fabric pour le
futur data lake — fonctionnement local sans compte cloud, coût,
reproductibilité pour un évaluateur tiers. Confirmée par la veille
technique du même jour.</div>
</div>

---
layout: default
---

# C4 — Veille technique et réglementaire

<div class="flex items-center gap-2">
<img src="/icons/news.svg" class="h-6">
<p class="text-sm"><code>docs/architecture/veille_technique_reglementaire.md</code> — journal hebdomadaire sur <b>3 semaines</b></p>
</div>

<div class="grid grid-cols-2 gap-4 mt-4">
<div class="p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
<b>Technique</b> — DataOps / ETL<br/>
<span class="opacity-80">Ex. : Airflow/Dagster/Prefect comparés face à des scripts Python + cron — disproportionné pour le volume du programme</span>
</div>
<div class="p-3 rounded bg-orange-500/10 border border-orange-500/30 text-sm">
<b>Réglementaire</b> — RGPD / RGAA<br/>
<span class="opacity-80">Ex. : recommandations CNIL sur la géolocalisation de flotte — confirme le niveau de risque RGPD retenu dès l'étude de faisabilité</span>
</div>
</div>

<div class="mt-4 text-sm opacity-70">Chaque entrée reliée à une décision réelle du programme — pas un exercice isolé.</div>

---
layout: default
---

# C5 — Planifier la réalisation

<div class="grid grid-cols-[36%_64%] gap-6 items-center mt-4">
<div>
<p class="text-sm"><code>docs/architecture/feuille_de_route.md</code></p>
<ul class="text-sm mt-3 space-y-1">
<li>4 phases ↔ 4 blocs de compétences</li>
<li>Composition d'équipe</li>
<li>Budget prévisionnel : <b>180 000 €</b></li>
<li>Gantt / PERT en <b>Mermaid</b> (texte versionné)</li>
<li>Suivi : GitHub Projects</li>
</ul>
</div>
<div>
<img src="/images/feuille_de_route_gantt.png" class="w-full rounded">
</div>
</div>

---
layout: default
---

# C6 — Superviser la réalisation

<div class="grid grid-cols-[55%_45%] gap-6 items-center mt-2">
<div>
<p class="text-sm"><code>docs/architecture/supervision_projet.md</code></p>
<ul class="text-sm mt-2 space-y-1">
<li>Rituels d'équipe : point hebdomadaire, comité de suivi mensuel</li>
<li>Tableau de suivi budgétaire actualisé à chaque jalon</li>
</ul>
<div class="mt-3 p-3 rounded bg-green-500/10 border border-green-500/30 text-sm">
Budget du périmètre initial (180 000 €) consommé intégralement sur
l'ensemble du programme (M0 à M4) — <b>aucun dépassement</b>.
</div>
</div>
<img src="/illustrations/presentation.svg" class="w-full">
</div>

---
layout: default
---

# Workflow Git

<div class="flex items-center gap-2 text-sm opacity-80">
<img src="/logos/github.svg" class="h-5 flex-shrink-0">
<span><code>main</code> protégée · <code>dev</code> intégration continue · <code>feat-&lt;n&gt;-&lt;slug&gt;</code> par issue ·
CI : <code>ruff</code> → <code>mypy</code> → <code>pytest</code> (176 tests) · GitHub Projects (6 statuts)</span>
</div>

<div class="mt-3">
<div class="text-xs opacity-60">1. Développement, jusqu'à la CI</div>
<img src="/images/supervision_projet_cycle_de_vie_1_developpement.png" class="w-full rounded">
</div>

<div class="mt-2">
<div class="text-xs opacity-60">2. Revue et intégration, jusqu'à la release</div>
<img src="/images/supervision_projet_cycle_de_vie_2_integration.png" class="w-full rounded">
</div>

<!--
Le mécanisme d'automatisation "linked PR" a été essayé puis abandonné le
25/08/2026 : trop rigide pour les PR de release qui ferment plusieurs
issues à la fois.
-->

---
layout: default
---

# C7 — Communiquer tout au long du projet

<div class="grid grid-cols-[55%_45%] gap-6 items-center mt-2">
<div>
<p class="text-sm"><code>docs/architecture/communication_lancement.md</code></p>
<ul class="text-sm mt-2 space-y-1">
<li>Plan de communication aux parties prenantes à chaque étape clé</li>
<li>Attention portée à l'accessibilité des documents partagés (RGAA)</li>
</ul>
</div>
<img src="/illustrations/conference-call.svg" class="w-full">
</div>

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

<img src="/illustrations/delivery-truck.svg" class="mx-auto mt-6 h-40">

<!-- Clos le 27/08/2026 (M1). Calibré sur E4 (15'). -->

---
layout: default
---

# Pourquoi extraire avant de modéliser ?

<div class="grid grid-cols-2 gap-4 mt-6">
<div class="p-3 rounded border-2 border-gray-400/30">
<div class="text-xs opacity-60 mb-2 text-center">Approche classique</div>
<div class="text-sm text-center">Concevoir le schéma de la base <b>d'abord</b>, à partir de la documentation des sources</div>
<div class="mt-2 text-xs text-center opacity-70">Risque : le schéma ne tient pas compte de ce que les données réelles révèlent</div>
</div>
<div class="p-3 rounded border-2 border-green-500/40 bg-green-500/5">
<div class="text-xs opacity-60 mb-2 text-center">Approche retenue</div>
<div class="text-sm text-center">Extraire et nettoyer <b>d'abord</b> (C8, C10, C9), modéliser <b>ensuite</b> (C11) à partir des données réelles</div>
<div class="mt-2 text-xs text-center opacity-70">Le taux de doublons mesuré (13-17 %, slide précédente) n'était connu qu'après extraction</div>
</div>
</div>

<div class="text-xl text-center mt-6 font-bold">
C8 → C10 → C9 → C11 → C12
</div>

<div class="mt-2 text-xs text-center opacity-60">
<code>docs/architecture/sequencement_bloc2.md</code> — C9/C10 indépendants, menés en parallèle
</div>

---
layout: default
---

# C8 — Automatiser l'extraction

<div class="text-sm">
5 connecteurs, 31 tests : API REST (TransFlow) · Scraping du portail
transporteur · Requêtes SQL directes (FluxPro) · Fichiers clients
hétérogènes · Historique volumineux
</div>

<div class="mt-4 flex justify-center">
<img src="/images/diagrammes_techniques_ingestion_c8.png" class="rounded" style="max-height: 390px; width: auto;">
</div>

<div class="mt-2 text-sm opacity-70">→ Démo live à ce point (voir issue #98)</div>

---
layout: default
---

# C9 — Requêtes SQL d'extraction

<img src="/illustrations/alarm-clock.svg" class="abs-tr mr-16 mt-2 h-28">

<p class="text-sm" style="max-width: 78%;"><code>docs/architecture/requetes_sql_extraction.md</code> — 5 requêtes documentées avec leurs résultats réels</p>

```sql
-- Expéditions en retard : alimente directement l'indicateur
-- « taux de service » attendu par la Direction des Opérations
SELECT exp.tracking_number, exp.transporteur, c.nom AS client,
       exp.date_livraison_prevue, exp.date_livraison_reelle,
       (exp.date_livraison_reelle - exp.date_livraison_prevue) AS jours_retard
FROM expeditions exp
JOIN commandes cmd ON cmd.id = exp.commande_id
JOIN clients c ON c.id = cmd.client_id
WHERE exp.date_livraison_reelle > exp.date_livraison_prevue
ORDER BY jours_retard DESC;
```

<div class="mt-4 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
Historique chargé dans la base de staging PostgreSQL existante, pas dans
un outil « big data » séparé : au volume réel (25 000 lignes), disproportionné —
choix de sobriété numérique (RGESN), pas de principe.
</div>

---
layout: default
---

# C10 — Règles d'agrégation : le bon grain compte

<div class="grid grid-cols-[66%_34%] gap-4 items-start">
<div>

```python
grain_counts = Counter((r[key], r[prod_key]) for r in rows)
true_dups = {k: v for k, v in grain_counts.items() if v > 1}
```

</div>
<img src="/illustrations/spreadsheets.svg" style="max-height: 160px; width: auto; margin: 0 auto; display: block;">
</div>

<div class="grid grid-cols-2 gap-4 mt-4">
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
layout: default
---

# C11 — Créer une base de données

<div class="grid grid-cols-[34%_66%] gap-4 items-center mt-4">
<div>
<p class="text-sm">Méthode MERISE, versionnée via Alembic</p>
<ul class="text-sm mt-3 space-y-2">
<li>2 violations de formes normales trouvées <b>empiriquement</b>, corrigées</li>
<li>Clé de rapprochement <code>tracking_number</code> (livraisons ↔ expéditions), <b>sans FK formelle</b> — systèmes sources distincts</li>
</ul>
</div>
<div class="flex justify-center">
<img src="/images/modelisation_merise_mcd.png" class="rounded" style="max-height: 420px; width: auto; max-width: 100%;">
</div>
</div>

---
layout: default
---

# C12 — Partager le jeu de données

<div class="grid grid-cols-[40%_60%] gap-6 items-center mt-4">
<div>
<div class="flex items-center gap-2">
<img src="/logos/fastapi.svg" class="h-6">
<p class="text-sm">API <b>Omega Data</b> (FastAPI → OpenAPI auto-générée)</p>
</div>
<p class="text-sm mt-2">Authentification par clé, autorisation par rôle.</p>
<div class="mt-3 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
Un référent client externe n'est pas <i>rejeté</i> s'il demande un autre
client — il est <i>silencieusement ramené</i> à son propre périmètre.
Vérifié en conditions réelles.
</div>
</div>
<div>
<img src="/images/diagrammes_techniques_api_sequence_autorisation.png" class="w-full rounded">
</div>
</div>

---
layout: default
---

# C12 — Documentation interactive (Swagger)

<div class="flex justify-center mt-4">
<img src="/images/swagger_omega_data_api.png" class="rounded border border-gray-300" style="max-height: 450px; width: auto;">
</div>

<div class="mt-2 text-xs text-center opacity-60"><code>localhost:8000/docs</code> — spécification OpenAPI générée automatiquement par FastAPI, testable directement dans le navigateur</div>

---
layout: default
---

# Point ouvert → transmis au Bloc 3

<div class="grid grid-cols-[1fr_auto_1fr] gap-4 items-center mt-10">
<div class="p-4 rounded border-2 border-blue-500/40 text-center">
<div class="text-xs opacity-60 mb-1">FluxPro</div>
<code class="text-sm">clients.nom</code>
<div class="text-sm mt-2">« NordDrive SARL »</div>
</div>
<div class="text-center text-2xl opacity-50">⇢ ?</div>
<div class="p-4 rounded border-2 border-orange-500/40 text-center">
<div class="text-xs opacity-60 mb-1">Historique (texte libre)</div>
<code class="text-sm">historique_expeditions.client</code>
<div class="text-sm mt-2">« NordDrive »</div>
</div>
</div>

<div class="mt-10 text-sm">
Rapprochement <b>cohérent sur le jeu de données actuel</b>, mais
<b>non garanti par une contrainte formelle</b> — pas de clé étrangère
possible entre deux libellés texte de systèmes sources distincts.
Signalé explicitement pour traitement lors de la modélisation de
l'entrepôt (Bloc 3).
</div>

---
layout: section
---

# Bloc 3 — Entrepôt OMEGA BI
## C13-C17 — ~15-20' (avec temps d'échange)

<img src="/illustrations/database-tables.svg" class="mx-auto mt-6 h-40">

<!-- Clos le 21/09/2026 (M2). Calibré sur E5 (10') + E6 (5-10', échange). -->

---
layout: default
---

# Séquencement retenu

`docs/architecture/sequencement_bloc3.md`

<div class="text-2xl text-center mt-6 font-bold">
C13 → C14 → C15 → C17 → C16
</div>

<div class="grid grid-cols-[1fr_auto_1fr] gap-4 items-center mt-6">
<div class="p-3 rounded border-2 border-blue-500/40 text-center text-sm">
<b>C17</b> — historiser <code>Dim_Client</code> (SCD2)
</div>
<div class="text-center text-xl opacity-50">→</div>
<div class="p-3 rounded border-2 border-green-500/40 text-center text-sm">
<b>C16</b> — purge RGPD <i>sur les versions historisées</i>
</div>
</div>

<div class="mt-6 p-4 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
Inversion volontaire par rapport au Gantt initial : la purge RGPD (C16)
ne peut porter que sur un schéma <b>déjà historisé</b> — il faut donc que
C17 l'ait créé avant.
</div>

---
layout: default
---

# C13 — Modéliser l'entrepôt

<div class="grid grid-cols-[40%_60%] gap-6 items-center mt-4">
<div>
<p class="text-sm">Approche bottom-up Kimball : <b>2 datamarts, 3 faits, 6 dimensions conformées</b></p>
<div class="mt-3 text-sm">
<b>Pourquoi pas de <code>Fait_Livraison</code> séparée ?</b><br/>
100 % des 1100 expéditions FluxPro ont exactement une livraison TransFlow
correspondante (1:1 vérifié empiriquement) — scinder aurait imposé une
jointure fait-à-fait à chaque requête.
</div>
</div>
<div>
<img src="/images/modelisation_omega_bi_mcd.png" class="w-full rounded">
</div>
</div>

---
layout: default
---

# C14 — Créer l'entrepôt

<div class="grid grid-cols-[34%_66%] gap-4 items-center mt-4">
<div>
<p class="text-sm">PostgreSQL, instance partagée avec le staging (sobriété RGESN)</p>
<p class="text-sm mt-2">5 schémas : <code>dimensions</code>, <code>exploitation</code>, <code>commercial</code>, <code>gouvernance</code>, <code>monitoring</code></p>
<div class="mt-3 text-sm opacity-70">
Cycle upgrade/downgrade vérifié contre une base réelle — un bug latent
Alembic (<code>include_schemas=True</code>) n'a été révélé qu'à la
seconde migration.
</div>
</div>
<div class="flex justify-center">
<img src="/images/creation_entrepot_omega_bi_schemas.png" class="rounded" style="max-height: 420px; width: auto; max-width: 100%;">
</div>
</div>

---
layout: default
---

# C15 — Développer des pipelines de données

<div class="grid grid-cols-[55%_45%] gap-6 items-center mt-2">
<div>
<p class="text-sm">Pipeline ETL staging → entrepôt</p>
<ul class="text-sm mt-2 space-y-2">
<li>Contrôles qualité réels : mise en <b>quarantaine</b> des lignes non rapprochées</li>
<li>Cohérence vérifiée par <b>double calcul indépendant</b> : ETL (C15) et API (C12) partent de la <b>même base de staging</b> (C11) — deux chemins de calcul distincts, même résultat</li>
</ul>
</div>
<img src="/illustrations/filter.svg" class="w-full">
</div>

---
layout: default
---

# C16 — Gestion opérationnelle

`docs/architecture/gestion_operationnelle_omega_bi.md`

```bash
# scripts/backup_omega_bi.sh --partiel|--complet
trap journaliser_echec ERR   # enregistre l'échec AVANT la fin du script
pg_dump -U "$PG_USER" -d "$OMEGA_BI_DB" \
  --table=dimensions.dim_client > "$FICHIER"   # --partiel : la seule table non reconstructible
```

- Backup (`pg_dump`) déclenché par `cron` (partiel quotidien / complet hebdomadaire) — 7 des 8 tables reconstructibles depuis le staging
- Journalisation réelle (`gouvernance`), connexion dédiée (survit à un `ROLLBACK`)
- Registre RGPD : audit automatisé répétable, aucune donnée personnelle trouvée

<div class="mt-3 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
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

<div class="mt-3 text-xs overflow-x-auto">

| client_key | nom | secteur | valid_from | valid_to | is_current |
|---|---|---|---|---|---|
| 42 | NordDrive SARL | Automobile | 2026-01-01 | **2026-06-14** | **false** |
| **87** | **NordDrive Group** | **Automobile** | **2026-06-15** | — | **true** |

</div>
<div class="text-xs opacity-60 mt-1">Changement de <code>nom</code> le 15/06 → ligne 42 close, ligne 87 ouverte ; les faits déjà chargés avant cette date référencent toujours <code>client_key=42</code></div>

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

<img src="/illustrations/secure-server.svg" class="mx-auto mt-6 h-40">

<!-- Clos le 23/09/2026 (M3). Calibré sur E7 (10'). -->

---
layout: default
---

# C18 — Architecture du data lake

<div class="text-sm">
Les données sont bien <b>copiées</b> dans <code>raw/</code> (copie fidèle
octet pour octet, C19) — <b>schema-on-read</b> ne veut pas dire « pas de
copie », mais que la <b>structure</b> (colonnes, types) n'est interprétée
qu'à la <b>lecture</b> (DuckDB), jamais imposée à l'écriture comme en
schema-on-write (staging/entrepôt). Flux IoT en ingestion directe,
<b>jamais</b> par la base de staging relationnelle — la zone
<code>curated/</code> se joint à la lecture aux dimensions conformées de
l'entrepôt.
</div>

<div class="mt-4">
<img src="/images/architecture_omega_lake_trois_couches.png" class="w-full rounded">
</div>

---
layout: default
---

# C18 — Zones raw / staging / curated

<div class="grid grid-cols-[32%_68%] gap-4 items-center mt-4">
<div class="text-sm">
<p><code class="break-all">docs/architecture/architecture_omega_lake.md</code></p>
<p class="mt-2">Clés naturelles de jointure vérifiées dans les données, jamais supposées.</p>
</div>
<div class="flex justify-center">
<img src="/images/architecture_omega_lake_zones.png" class="rounded" style="max-height: 420px; width: auto; max-width: 100%;">
</div>
</div>

---
layout: default
---

# C19 — Intégrer l'infrastructure

<div class="flex items-center gap-3 mb-2">
<img src="/logos/minio.svg" class="h-7">
<img src="/logos/duckdb.svg" class="h-7">
<span class="text-sm">MinIO (S3) + <b>DuckDB</b> (jointures) + <b>boto3</b> (copie fidèle de <code>raw/</code>)</span>
</div>

<div class="mt-3 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
<b>Pourquoi pas pandas ?</b> <code>pandas.read_sql()</code> existe, mais
charge d'abord un DataFrame complet en mémoire avant de pouvoir joindre —
pas de langage de requête, juste des appels d'API. Aurait aussi introduit
une dépendance que le projet n'utilise nulle part ailleurs (vérifié par
grep avant de choisir). DuckDB s'aligne avec l'existant : requêtes SQL
directes, comme le reste du projet interroge déjà PostgreSQL.
</div>

<div class="mt-3 p-3 rounded bg-orange-500/10 border border-orange-500/30 text-sm">
DuckDB peut reformater silencieusement un CSV/JSON en le réécrivant —
incompatible avec la garantie « octet pour octet » de <code>raw/</code>
(vérifiée par somme de contrôle SHA-256). <code>boto3</code> transfère
des octets sans les interpréter.
</div>

<div class="grid grid-cols-[62%_38%] gap-4 items-center mt-3">
<div class="text-sm">
<b>Flux SSE</b> fenêtré par intervalle de 5 minutes, vérifié par <b>coupure
brutale réelle</b> (<code>kill -9</code> puis redémarrage) : aucune collision, aucune
donnée corrompue.
</div>
<img src="/illustrations/video-streaming.svg" style="max-height: 130px; width: auto; margin: 0 auto;">
</div>

---
layout: default
---

# C19 — MinIO en conditions réelles

<div class="flex items-center gap-2 mb-2">
<img src="/logos/minio.svg" class="h-6">
<span class="text-sm"><code>localhost:9001</code> — console web, bucket <code>omega-lake</code></span>
</div>

<div class="flex justify-center">
<img src="/images/minio_console_buckets.png" class="rounded border border-gray-300" style="max-height: 400px; width: auto;">
</div>

<div class="mt-2 text-xs text-center opacity-60">4 zones visibles comme de vrais préfixes S3 : <code>raw/</code>, <code>staging/</code>, <code>curated/</code>, <code>curated_bi/</code> (export pseudonymisé, C21)</div>

---
layout: default
---

# C20 — Catalogue de données

```python
schema_brut = con.sql(f"DESCRIBE SELECT * FROM {lecture}").fetchall()
nb_lignes = con.sql(f"SELECT count(*) FROM {lecture}").fetchone()[0]
derniere_modification = max(o["LastModified"] for o in objets)
```

Généré par **introspection réelle** (`boto3` + `DESCRIBE` DuckDB), jamais
maintenu à la main — même principe que l'audit RGPD automatisé de C16 :
un catalogue généré ne peut pas devenir silencieusement obsolète.

<div class="mt-4 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
Le catalogue couvre <code>staging/</code> et <code>curated/</code>, pas
seulement <code>raw/</code> — périmètre volontairement élargi pour un
catalogue réellement exploitable (schéma, volumétrie, fraîcheur par
flux), pas une simple liste de fichiers bruts.
</div>

<div class="mt-3 text-xs">
Exemple de sortie réelle (une entrée, flux SSE capteurs) :

```json
{"flux": "flux_sse_capteurs", "zone": "curated", "source": "api-mock",
 "format": "parquet", "nb_lignes": 48213,
 "schema": [{"colonne": "vehicule_id", "type": "VARCHAR"}, {"colonne": "temperature", "type": "DOUBLE"}, "..."],
 "derniere_modification": "2026-10-20T14:32:07"}
```
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

<div class="grid grid-cols-[1fr_auto_1fr_auto_1fr] gap-2 items-center mt-3 text-xs text-center">
<div class="p-2 rounded border border-gray-400/30"><code>vehicule_id</code><br/>"VH-007"</div>
<div class="opacity-50">+ clé secrète →</div>
<div class="p-2 rounded border border-blue-500/40 bg-blue-500/5">HMAC-SHA256</div>
<div class="opacity-50">→</div>
<div class="p-2 rounded border border-green-500/40 bg-green-500/5"><code>curated_bi/</code><br/>"a3f9...e21c"</div>
</div>
<div class="text-xs text-center opacity-60 mt-1"><code>curated/</code> (original) reste inaccessible au rôle <code>lake_reader</code>, qui ne voit que <code>curated_bi/</code> (pseudonymisé)</div>

1. Risque identifié dès C18 (recoupement géoloc ↔ chauffeur)
2. Première analyse incomplète — écartée, puis **réintroduite** après vérification approfondie
3. HMAC implémenté — hash simple = recalculable par force brute sur 15 véhicules
4. Repli codé en dur trouvé lors d'un **second contrôle** → garde-fou `verifier_cle_configuree()`
5. Risque résiduel assumé (stabilité de la clé entre exécutions) — documenté, pas masqué

---
layout: section
---

# M4 — Restitution BI (Grafana)
## + synthèse transverse + conclusion — ~10-15'

<img src="/illustrations/growth-analytics.svg" class="mx-auto mt-6 h-40">

---
layout: default
---

# Pourquoi M4 ? Compléter, pas corriger

<div class="grid grid-cols-2 gap-4 mt-4 text-sm">
<div class="p-3 rounded border border-gray-400/30">
<b>Notebook SLA (C16)</b><br/>
<span class="opacity-80">Preuve exploratoire à la clôture du Bloc 3 — gardé tel quel, jamais retiré ni réécrit</span>
</div>
<div class="p-3 rounded border border-gray-400/30">
<b>Vues SQL (C16)</b><br/>
<span class="opacity-80">KPIs réels, interrogeables — la donnée de référence, déjà correcte</span>
</div>
</div>

<div class="mt-4 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
Référentiel C16 exige un <b>tableau de bord</b> ; référentiel C20 exige un
<b>monitorage actif avec alerte</b>. Un notebook exploratoire et des vues
SQL interrogeables ne satisfont pas littéralement ces deux formats précis
— écart de <i>forme</i>, pas de <i>fond</i>, repéré en relisant le
référentiel à la lettre après la clôture de M2/M3.
</div>

Grafana, auto-hébergé, ajouté <b>en complément</b> — seule forme satisfaisant
littéralement les deux critères. Décidé avant Power BI (cloud) ou Databricks (workspace dédié).

---
layout: default
---

# Infrastructure : un seul `docker-compose.yml`

<div class="flex items-center gap-2 mb-3">
<img src="/logos/docker.svg" class="h-6">
<code class="text-sm">docker compose -f infra/docker/docker-compose.yml --env-file .env up -d</code>
</div>

| Service | Port | Accès |
|---|---|---|
| PostgreSQL (staging + entrepôt) | 5432 | `psql` ou client SQL |
| API Omega Data (FastAPI) | 8000 | `localhost:8000/docs` |
| MinIO (console web) | 9001 | `localhost:9001` |
| Grafana | 3000 | `localhost:3000` |
| MailHog (boîte de réception des alertes) | 8025 | `localhost:8025` |

<div class="flex items-center gap-6 mt-4">
<img src="/logos/postgresql.svg" class="h-8">
<img src="/logos/fastapi.svg" class="h-8">
<img src="/logos/minio.svg" class="h-8">
<img src="/logos/grafana.svg" class="h-8">
</div>

<div class="mt-4 text-sm opacity-70">
Auto-hébergé, sans dépendance à un service cloud — cohérent avec la
sobriété numérique (RGESN) retenue dès C3. Mots de passe injectés via
<code>--env-file .env</code>, jamais codés en dur.
</div>

---
layout: default
---

# C16bis — Restitution OMEGA BI

<div class="grid grid-cols-[42%_58%] gap-6 items-center mt-4">
<div>
<p class="text-sm">Dashboard Grafana connecté en lecture seule (<code>bi_reader</code>)</p>
<ul class="text-sm mt-3 space-y-2">
<li>Taux de service par client : <b>FreshMarket 90,6 %</b>, <b>NordDrive 87,5 %</b>, <b>MedioTex 87,3 %</b></li>
<li>Délai moyen de livraison par transporteur</li>
<li>Quantité expédiée par entrepôt (Lyon, Lille, Marseille)</li>
</ul>
</div>
<div>
<img src="/images/gestion_operationnelle_omega_bi_dashboard_grafana.png" class="w-full rounded">
</div>
</div>

---
layout: default
---

# C20bis — Monitorage du data lake

```python
def verifier_sante_infrastructure(s3, dsn, bucket) -> dict:
    try:
        capacite = sum(o["Size"] for page in paginator.paginate(Bucket=bucket)
                        for o in page.get("Contents", []))
        accessible = True
    except Exception:
        accessible, capacite = False, None  # l'échec EST le résultat à enregistrer
    # ... INSERT dans monitoring.sante_infrastructure
    return {"minio_accessible": accessible, "capacite_utilisee_octets": capacite}
```

Relevé de santé infrastructure (MinIO, capacité) + règle d'alerte Grafana réelle

<div class="flex items-center gap-2 text-sm">
<img src="/logos/grafana.svg" class="h-6">
<span>→ service interne authentifié → <code>smtplib</code> →</span>
<img src="/icons/mail.svg" class="h-6">
<span>MailHog</span>
</div>

<div class="mt-3 p-3 rounded bg-green-500/10 border border-green-500/30 text-sm">
Testé de bout en bout, deux fois : coupure réelle de MinIO → alerte
active en ~30s → e-mail reçu dans MailHog. Remise en service → alerte résolue.
</div>

<div class="mt-2 flex justify-center">
<img src="/images/mailhog_alerte_minio.png" class="rounded border border-gray-300" style="max-height: 105px; width: auto;">
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
d'équivalent. Documenté au chapitre 6 du rapport, suivi par l'issue #104
(backlog, à traiter si le temps le permet).
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

<div class="flex items-start gap-3">
<img src="/icons/shield.svg" class="h-6 flex-shrink-0 mt-1">
<div class="text-sm"><b>RGPD</b> — la pseudonymisation (C21) : risque identifié → analyse
incomplète écartée → réintroduite après vérification approfondie →
faille (repli codé en dur) trouvée lors d'un second contrôle →
risque résiduel assumé</div>
</div>
<div class="flex items-start gap-3 mt-3">
<img src="/icons/leaf.svg" class="h-6 flex-shrink-0 mt-1">
<div class="text-sm"><b>RGESN</b> — critère invoqué à chaque choix d'infrastructure
(pas de « big data » séparé, pas d'orchestrateur, outils auto-hébergés)</div>
</div>
<div class="flex items-start gap-3 mt-3">
<img src="/icons/accessible.svg" class="h-6 flex-shrink-0 mt-1">
<div class="text-sm"><b>RGAA</b> — accessibilité appliquée en continu aux livrables
Markdown/PDF, pas vérifiée une seule fois en fin de programme</div>
</div>

<div class="mt-6 text-sm font-bold">
Motif qui se répète : chaque étape déclenchée par un contrôle qualité
supplémentaire qui trouve un défaut dans l'étape précédente — jamais un
audit générique ponctuel.
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

<img src="/illustrations/completed-steps.svg" class="mx-auto mt-6 h-32">

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
- **Le contrôle qualité à plusieurs niveaux comme détecteur d'angles
  morts** — la restitution BI (M4) et la faille de repli codé en dur ont
  toutes deux été trouvées lors d'une vérification approfondie, alors
  qu'une première analyse les avait jugées suffisantes

<img src="/illustrations/team-collaboration.svg" class="mx-auto mt-6 h-40">

<!--
Ne pas écrire "assistance IA" sur la slide -- si la question est posée à
l'oral, le dire directement : chaque décision structurante a été arbitrée
et validée par le Data Engineer, jamais déléguée. Historique Git public
disponible. Mieux à l'oral qu'à l'écrit (décision du 22/10/2026).
-->

---
layout: center
class: text-center
---

# Questions & échanges avec le jury

<div class="opacity-70 mt-4">~10' — ouvert à tous les blocs</div>

---
layout: end
---

<img src="/illustrations/handshake-deal.svg" class="mx-auto h-40">

# Merci

<div class="opacity-70">
Dépôt public : github.com/alaugier/datacore
</div>
