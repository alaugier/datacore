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

# DATA CORE

Refonte de l'infrastructure data d'Omega Logistics

<div class="pt-8 opacity-80">
Alexandre Laugier — Certification Data Engineer (RNCP37638)
</div>

<div class="abs-bl ml-8 mb-8 bg-white rounded-lg px-4 py-2 inline-block">
<img src="/images/simplon_logo.png" class="h-6">
</div>

<!--
- Se présenter : nom, certification visée (Data Engineer, RNCP37638)
- Annoncer le plan en une phrase : 4 blocs de compétences + jalon transverse M4
- Durée visée ~90-100 min, sans s'excuser du temps
- Ne pas lire le sous-titre à voix haute, juste enchaîner
-->

---
layout: default
---

# Sommaire — ~90-100 minutes

| Section | Durée visée |
|---|---|
| [Contexte Omega Logistics / DATA CORE](3) | ~5' |
| [Bloc 1 — Cadrage (C1-C7)](6) | ~30-35' |
| [Bloc 2 — Collecte & Stockage (C8-C12), avec démonstration](16) | ~15' |
| [Bloc 3 — Entrepôt OMEGA BI (C13-C17), avec temps d'échange dédié](25) | ~15-20' |
| [Bloc 4 — Data Lake OMEGA LAKE (C18-C21)](34) | ~10' |
| [M4 (Grafana) + synthèse transverse + conclusion](41) | ~10-15' |
| [Questions & échanges avec le jury](53) | ~10' |

<!--
- Annoncer le minutage par section une seule fois ici, pas à répéter ensuite
- Préciser que ce minutage est calé sur le déroulé E1-E7 de la certification
- Ne pas s'excuser si le minutage glisse en cours de route
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
- Présenter Omega Logistics en une phrase : 3PL, 3 sites, 3 clients aux besoins très différents
- Nommer le commanditaire (Éléonore RAKOTO, Directrice des Opérations) et le sponsor (Karim BELAÏD, Pôle Data)
- Le vrai problème métier : dispersion → erreurs récurrentes + pas de vision consolidée (pas juste "deux vieux systèmes")
- FluxPro = WMS (entrepôts) / TransFlow = TMS (tournées) — ne pas les inverser à l'oral
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
- Lire les 5 objectifs au fil du slide, sans les reformuler un par un
- Dire dès maintenant que l'objectif 3 a nécessité un détour (vues SQL/notebook → Grafana M4) — anticiper plutôt que laisser découvrir
- Sigles SMART/RICE en note de bas de page : les lire seulement si le jury le demande
- Insister sur le schéma : c'est RICE qui a arbitré le séquencement des 4 blocs, pas un choix arbitraire
-->

---
layout: default
---

# Score RICE par chantier

<p class="text-xs opacity-60">Score = (Reach × Impact × Confidence) / Effort — <code>etude_faisabilite.md</code> §6</p>

<div class="flex flex-col gap-2 mt-5 text-sm" style="font-variant-numeric: tabular-nums;">
<div class="flex items-center gap-3">
<div style="width: 230px;">FluxPro + fichiers clients</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:100%; background:#1c7ed6;">13,5</div></div>
<span class="text-xs opacity-60" style="width:60px;">Prio. 1</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 230px;">Registre RGPD / pseudonymisation</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:67%; background:#1c7ed6;">9,0</div></div>
<span class="text-xs opacity-60" style="width:60px;">Prio. 2<sup>*</sup></span>
</div>
<div class="flex items-center gap-3">
<div style="width: 230px;">API REST consolidée</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:53%; background:#1c7ed6;">7,2</div></div>
<span class="text-xs opacity-60" style="width:60px;">Prio. 2</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 230px;">Portail transporteur (scraping)</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:36%; background:#1c7ed6;">4,8</div></div>
<span class="text-xs opacity-60" style="width:60px;">Prio. 4</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 230px;">Entrepôt OMEGA BI</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:35%; background:#1c7ed6;">4,7</div></div>
<span class="text-xs opacity-60" style="width:60px;">Prio. 3</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 230px;">Catalogue & gouvernance</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:15%; background:#1c7ed6;">2,0</div></div>
<span class="text-xs opacity-60" style="width:60px;">Prio. 5</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 230px;">Data lake OMEGA LAKE</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:9%; background:#1c7ed6;">1,2</div></div>
<span class="text-xs opacity-60" style="width:60px;">Prio. 5</span>
</div>
</div>

<div class="text-xs opacity-60 mt-3"><sup>*</sup> transverse, non séquençable — traité en continu sur les 4 blocs</div>

<!--
- Score RICE = (Reach × Impact × Confidence) / Effort — chiffres réels de l'étude de faisabilité §6, pas d'ordre de grandeur inventé
- FluxPro/clients en tête car Reach=10, Confidence=0,9, Effort=2 : gros volume, quasi-certain, peu coûteux
- Data lake en dernier car Confidence=0,5 (flux temps réel jamais fait) et Effort=5 (le plus lourd) — cohérent avec le choix de le traiter en bloc 4
- RGPD priorité 2 mais marqué transverse : pas séquencé comme les autres, traité en continu
-->

---
layout: section
---

# Bloc 1 — Cadrage
## C1-C7 — ~30-35'

<img src="/illustrations/route-planning.svg" class="mx-auto mt-6 h-40">

<!--
- Transition courte : "Premier bloc, le cadrage — 7 compétences, clos le 25/08"
- Ne pas s'attarder sur cette slide, enchaîner vite sur C1
-->

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

<!--
- Citer les 3 types d'entretiens : commanditaire, sponsor, responsables d'entrepôt
- Ordre réel de la méthode : RICE priorise, SMART formule les objectifs ensuite
- Point clé à redire : c'est cette analyse RICE qui arbitre l'ordre des 4 blocs (collecte avant entrepôt avant lake)
-->

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

<!--
- Insister : sources explorées directement dans le code (data/raw/, api-mock/), pas depuis une description théorique
- Citer les 7 sources si le temps le permet, sinon renvoyer au schéma affiché
- Les 2 flux IoT anticipent le Bloc 4 — le dire explicitement, ça crée un fil avec la suite
-->

---
layout: default
---

# C3 — Concevoir un cadre technique d'exploitation

<div class="grid grid-cols-[62%_38%] gap-4 items-center">
<div>
<p class="text-sm"><code>docs/architecture/architecture_cible.md</code></p>
<ul class="text-sm mt-2 space-y-1">
<li>Cible AS IS / TO BE, matrice des flux</li>
<li>Registre RGPD préliminaire par brique technique</li>
<li>Stratégie RGESN (éco-conception) et RGAA (accessibilité)</li>
</ul>
</div>
<img src="/illustrations/building-blocks.svg" style="max-height: 200px; width: auto; margin: 0 auto; display: block;">
</div>

<div class="mt-5 p-3 rounded bg-blue-500/10 border border-blue-500/30 flex items-center gap-4">
<img src="/logos/minio.svg" class="h-10 flex-shrink-0">
<div><b>Décision structurante :</b> MinIO plutôt que Microsoft Fabric pour le
futur data lake — fonctionnement local sans compte cloud, coût,
reproductibilité pour un évaluateur tiers. Confirmée par la veille
technique du même jour.</div>
</div>

<!--
- La décision MinIO vs Microsoft Fabric est LE choix structurant de ce bloc — prendre le temps de la détailler
- 3 raisons dans l'ordre : pas de compte cloud, coût, reproductibilité pour un évaluateur tiers
- RGESN/RGAA : juste les citer ici, détaillés plus tard dans la synthèse transverse
-->

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
<b>Technique</b> — DataOps / ETL
<div class="mt-2 pl-2 border-l-2 border-blue-500/50">
<span class="text-xs font-bold uppercase tracking-wide opacity-70">Exemple concret</span><br/>
<span class="opacity-80">Airflow/Dagster/Prefect comparés face à des scripts Python + cron — disproportionné pour le volume du programme</span>
</div>
</div>
<div class="p-3 rounded bg-orange-500/10 border border-orange-500/30 text-sm">
<b>Réglementaire</b> — RGPD / RGAA
<div class="mt-2 pl-2 border-l-2 border-orange-500/50">
<span class="text-xs font-bold uppercase tracking-wide opacity-70">Exemple concret</span><br/>
<span class="opacity-80">Recommandations CNIL sur la géolocalisation de flotte — confirme le niveau de risque RGPD retenu dès l'étude de faisabilité</span>
</div>
</div>
</div>

<div class="grid grid-cols-[72%_28%] gap-4 items-center mt-4">
<div class="text-sm opacity-70">Chaque entrée reliée à une décision réelle du programme — pas un exercice isolé.</div>
<img src="/illustrations/search.svg" class="w-full">
</div>

<!--
- 3 semaines de veille, 2 axes : technique et réglementaire
- Donner l'exemple déjà affiché pour chaque axe (Airflow/Dagster/Prefect écartés ; CNIL géolocalisation) — pas besoin d'en improviser d'autres
- Le point à marteler : chaque entrée reliée à une décision réelle, pas un exercice scolaire isolé
-->

---
layout: default
---

# C5 — Planifier la réalisation

<div class="grid grid-cols-[31%_69%] gap-4 items-center mt-4">
<div>
<p style="font-size: 0.7rem; white-space: nowrap;"><code>docs/architecture/feuille_de_route.md</code></p>
<ul class="text-sm mt-3 space-y-1">
<li>4 phases ↔ 4 blocs de compétences</li>
<li>Composition d'équipe</li>
<li>Budget prévisionnel : <b>180 000 €</b></li>
<li>Gantt / PERT en <b>Mermaid</b> (texte versionné)</li>
<li>Suivi : GitHub Projects</li>
</ul>
<img src="/illustrations/five-year-plan.svg" class="mt-4" style="max-height: 150px;">
</div>
<div>
<img src="/images/feuille_de_route_gantt.png" class="w-full rounded">
</div>
</div>

<!--
- Montrer le Gantt du doigt, citer les 4 phases dans l'ordre
- Budget 180 000 € — le dire ici une première fois, sera repris en synthèse transverse
- GitHub Projects = outil de suivi réellement utilisé, pas juste mentionné sur le papier
-->

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

<!--
- Rituels d'équipe : point hebdomadaire + comité de suivi mensuel
- Point fort à marteler : budget consommé intégralement, 0 dépassement sur tout le programme
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

<!--
- Plan de communication aux parties prenantes à chaque étape clé
- RGAA appliqué aussi à la communication, pas seulement au code/aux documents techniques
-->

---
layout: fact
---

# 4 / 7

Compétences couvertes par le suivi GitHub initial du Bloc 1

<!--
- Annoncer le chiffre directement : 4 compétences sur 7 couvertes au départ
- Expliquer : trouvé en rédigeant le compte-rendu M0, PAS découvert après coup par un tiers
- Comblé par 3 issues supplémentaires (C4, C6, C7) avant de considérer le jalon clos
- Message clé : ce réflexe de vérification est resté constant sur tout le programme (cf. C20, Bloc 4)
-->

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
- Transition : "avant le Bloc 2, le processus qui a structuré tout le travail"
- Dans l'ordre : main protégée / dev intégration continue / feat-<n> par issue
- CI dans cet ordre précis : ruff → mypy → pytest (176 tests) — le dire si question technique
- Si interrogé sur "linked PR" : essayé puis abandonné le 25/08, trop rigide pour les PR de release qui ferment plusieurs issues à la fois
-->

---
layout: section
---

# Bloc 2 — Collecte & Stockage
## C8-C12 — ~15' (avec démonstration)

<img src="/illustrations/delivery-truck.svg" class="mx-auto mt-6 h-40">

<!--
- Transition rapide : "Bloc 2, collecte et stockage — 5 compétences, avec une démo prévue à C8"
- Prévenir le jury qu'une démonstration live arrive bientôt
-->

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

<img src="/illustrations/choice.svg" class="mx-auto mt-4 h-36">

<!--
- Poser le dilemme avant de donner la réponse : modéliser d'abord semble plus "propre" sur le papier
- La vraie raison du choix : le taux de doublons réel n'était pas connu avant d'extraire concrètement
- Préciser : C9/C10 sont indépendants, menés en parallèle — pas un ordre strictement imposé
-->

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

<!--
- 5 connecteurs, 31 tests — citer le chiffre
- Ne pas décrire chaque connecteur un par un, renvoyer au schéma affiché
- Lancer la démo live ici si le script est prêt (issue #98), sinon l'annoncer pour plus tard
- URLs utiles pour la démo : localhost:5050/portail-transporteur/colis (scraping, api-mock) et localhost:8000/docs (API Omega Data, FastAPI) — les deux sont listées sur la slide "Infrastructure"
-->

---
layout: default
---

# C9 — Requêtes SQL d'extraction

<div class="flex items-center gap-2 mb-1">
<div class="flex items-center gap-1.5 text-xs text-center flex-shrink-0">
<div class="flex flex-col items-center gap-0.5"><img src="/icons/clock-blue.svg" class="h-7"><span>prévue</span></div>
<span class="opacity-40 text-sm">≠</span>
<div class="flex flex-col items-center gap-0.5"><img src="/icons/clock-orange.svg" class="h-7"><span>réelle</span></div>
</div>
<p class="text-xs"><code>docs/architecture/requetes_sql_extraction.md</code> — 5 requêtes documentées avec leurs résultats réels</p>
</div>

<div style="font-size: 0.66em;">

```sql
-- Expéditions en retard : alimente l'indicateur « taux de service » (Direction des Opérations)
SELECT exp.tracking_number, exp.transporteur, c.nom AS client,
       exp.date_livraison_prevue, exp.date_livraison_reelle,
       (exp.date_livraison_reelle - exp.date_livraison_prevue) AS jours_retard
FROM expeditions exp
JOIN commandes cmd ON cmd.id = exp.commande_id
JOIN clients c ON c.id = cmd.client_id
WHERE exp.date_livraison_reelle > exp.date_livraison_prevue
ORDER BY jours_retard DESC;
```

</div>

<div class="text-xs leading-tight">
↳ produit (extrait réel) :

| tracking_number | transporteur | client | date_livraison_prevue | date_livraison_reelle | jours_retard |
|---|---|---|---|---|---|
| OMG0001333 | EcoRoute | NordDrive | 2025-08-30 | 2025-09-02 | 3 |
| OMG0000527 | RapidFret | MedioTex | 2025-07-30 | 2025-08-02 | 3 |

</div>

<div class="p-1 rounded bg-blue-500/10 border border-blue-500/30 text-xs leading-tight">
Historique chargé dans la base de staging PostgreSQL existante, pas dans un outil
« big data » séparé : au volume réel (25 000 lignes), disproportionné — choix de
sobriété numérique (RGESN), pas de principe.
</div>

<!--
- Montrer la requête affichée : expéditions en retard = date réelle > date prévue
- Relier explicitement à l'indicateur "taux de service" demandé par la Direction des Opérations
- Rappeler le choix RGESN : staging existant plutôt qu'un outil big data pour 25 000 lignes
-->

---
layout: default
---

# C10 — Règles d'agrégation : le bon grain compte

<div class="grid grid-cols-[55%_45%] gap-4 items-center">
<div>

```python
grain_counts = Counter((r[key], r[prod_key]) for r in rows)
true_dups = {k: v for k, v in grain_counts.items() if v > 1}
```

</div>
<div class="flex justify-center">
<img src="/illustrations/spreadsheets.svg" style="max-height: 150px; width: auto;">
</div>
</div>

<div class="mt-5">
<div class="text-xs opacity-60 text-center">Exemple réel — <code>norddrive_commandes.csv</code>, 2 lignes avec même <code>ref_commande</code></div>
<div class="flex justify-center items-center gap-6 mt-2">
<div class="p-2 rounded border-2 border-gray-400/40 text-sm">ND-000402</div>
<div class="flex flex-col gap-2 text-xs" style="position:relative;">
<div style="position:absolute; left:-24px; top:8px; width:24px; height:34px; border-top:2px solid #adb5bd; border-bottom:2px solid #adb5bd; border-left:2px solid #adb5bd; border-radius: 8px 0 0 8px;"></div>
<div class="flex items-center gap-2">
<div class="p-1.5 rounded border-2 border-green-500/40 bg-green-500/5">SKU-10009 · Rétroviseur</div>
<span class="opacity-60">couple distinct</span>
</div>
<div class="flex items-center gap-2">
<div class="p-1.5 rounded border-2 border-green-500/40 bg-green-500/5">SKU-10003 · Filtre à huile</div>
<span class="opacity-60">couple distinct</span>
</div>
</div>
</div>
</div>

<div class="grid grid-cols-2 gap-4 mt-4">
<div class="p-2.5 rounded bg-red-500/10 border border-red-500/30 leading-tight">
<b>Grain « commande » seul</b><br/>
55 à 68 % de doublons — chiffre trompeur (mesure le nombre moyen de
produits par commande)
</div>
<div class="p-2.5 rounded bg-green-500/10 border border-green-500/30 leading-tight">
<b>Grain (commande, produit)</b><br/>
13 à 17 % selon le client — taux réel, retenu et implémenté
(<code>deduplicate()</code>)
</div>
</div>

<!--
- LE moment clé de la présentation : annoncer d'abord le chiffre trompeur (55-68 %) avant de révéler le vrai (13-17 %)
- Expliquer la confusion : grain "commande" seul confond commandes multi-produits et vrais doublons
- Citer deduplicate() comme l'implémentation réelle, pas juste un calcul théorique
- Si question sur l'illustration (écran avec colonnes A/B/C/D) : c'est une image décorative (undraw), elle ne représente aucune donnée réelle du projet — l'exemple vérifiable est le bloc ND-000402 plus bas, séparé de l'illustration
-->

---
layout: default
---

# C11 — Créer une base de données

<div class="grid grid-cols-[34%_66%] gap-4 items-center mt-4">
<div>
<p class="text-sm">Méthode MERISE, versionnée via Alembic</p>
<ul class="text-sm mt-3 space-y-2">
<li>2 violations de formes normales trouvées <b>empiriquement</b>, corrigées :
  <code>livraisons.statut</code> (3NF, dépendance transitive → vue SQL) et
  <code>commandes_clients</code> (2NF, dépendance partielle → décomposée en-tête/lignes)</li>
<li>Clé de rapprochement <code>tracking_number</code> (livraisons ↔ expéditions), <b>sans FK formelle</b> — systèmes sources distincts</li>
</ul>
<div class="mt-2 p-2 rounded bg-gray-400/10 border border-gray-400/20 text-xs leading-tight">
<b>Clé métier</b>, pas une FK : un identifiant qui a un sens métier (<code>sku</code>,
<code>tracking_number</code>) sert à rapprocher des données — mais une <b>FK</b>
SGBD exige que la colonne visée soit PK ou UNIQUE (ce n'est pas le cas ici) —
à l'inverse de <code>commande_client_id</code>, FK classique vers une PK du
<i>même</i> schéma.
</div>
</div>
<div class="flex justify-center">
<img src="/images/modelisation_merise_mcd.png" class="rounded" style="max-height: 420px; width: auto; max-width: 100%;">
</div>
</div>

<!--
- Méthode MERISE, versionnée via Alembic — pas modélisée "dans la tête", tracée
- tracking_number : expliquer pourquoi pas de FK formelle (deux systèmes sources distincts, FluxPro et TransFlow)

PENSE-BÊTE "clé métier" (si le jury creuse le vocabulaire) :

- Définition : un identifiant qui a un sens dans le métier/le monde réel
  (ex. un SKU, un numéro de tracking), par opposition à une clé technique
  /de substitution (un entier auto-incrémenté sans signification métier,
  ex. commandes_clients.id). En anglais : "natural key" / "business key".
- PAS une simple convention : une contrainte FOREIGN KEY SGBD exige que
  la colonne référencée soit PK ou UNIQUE. Deux cas réels dans ce projet,
  deux raisons différentes :
  1. tracking_number (expeditions ↔ livraisons) : FluxPro et TransFlow
     sont deux systèmes distincts — aucune FK inter-base n'est possible.
     Vérif. SQL réelle (modelisation_merise.md §4.1) :
     SELECT count(*) FROM livraisons l JOIN expeditions e
       ON e.tracking_number = l.tracking_number; -- -> 1100 = 1100, 100%
  2. lignes_commande_clients.sku ↔ produits.sku : MÊME base de staging,
     mais produits.sku n'est pas contraint UNIQUE dans le schéma FluxPro
     fourni (seul produits.id est PK) -> Postgres refuse une FK dessus,
     même si la table est locale. Vérif. empirique : 0 ligne orpheline
     sur 3593 lignes importées (modelisation_merise.md §3.4). SQL réel
     utilisé en prod (src/datacore/api/repository.py) :
     JOIN produits p ON p.sku = lcc.sku
  - Contre-exemple : commandes_clients.commande_id n'est PAS une clé de
    rapprochement du tout — identifiant propre au client (ref_commande/
    id_commande_client/numero_cde), sans correspondance connue avec
    commandes.id FluxPro (deux processus métier distincts) ; modélisée
    comme entité indépendante, pas jointe (modelisation_merise.md §4.2).
  - commande_client_id (dans lignes_commande_clients), lui, EST une FK
    classique : il référence commandes_clients.id, une PK du même schéma.
- Origine / références si demandées : vocabulaire standard de modélisation
  relationnelle (candidate key, C.J. Date, "An Introduction to Database
  Systems"), popularisé en data warehousing par Kimball & Ross, "The Data
  Warehouse Toolkit" (clé naturelle/"business key" vs clé de substitution
  "surrogate key" — c'est tout l'argument derrière Dim_Client en C17,
  SCD2). Équivalent français : "clé entreprise"/clé naturelle, ex. Éditions
  ENI, "Modélisation BI et OLAP". Pas un terme MERISE officiel au sens
  strict — MERISE parle d'identifiant naturel vs technique, même notion.

PENSE-BÊTE détaillé des 2 violations (si le jury creuse) :

1. livraisons.statut — violation de 3NF (dépendance transitive entre deux attributs non-clés)
   - Hypothèse testée : statut est-il redondant avec heure_reelle ?
   - Vérifié sur les 1100 livraisons : heure_reelle renseignée → statut TOUJOURS "Livree" ; heure_reelle vide → TOUJOURS "En cours"
   - Corrélation 100 %, sans exception → statut est déterminé par heure_reelle, pas par la clé
   - Corrigé par une VUE SQL (livraisons_avec_statut), pas une colonne stockée : élimine la redondance physique, pas juste le risque d'incohérence

2. commandes_clients — violation de 2NF (dépendance partielle sur une clé composite)
   - Table plate initiale, clé naturelle (client, commande_id, sku)
   - Testé : libelle_produit, poids_kg, chaine_froid_requise dépendent de sku SEUL (pas besoin de client+commande_id) — 0 exception sur 30 sku
   - Testé : date_commande, entrepot dépendent de (client, commande_id) SEUL (pas besoin de sku) — 0 exception sur 1396 commandes
   - Bonus trouvé en vérifiant : ces attributs étaient aussi entièrement redondants avec produits.libelle/poids_kg/temperature_dirigee côté FluxPro (0 écart)
   - Corrigé par décomposition en-tête (commandes_clients) / lignes (lignes_commande_clients), même principe que FluxPro
-->

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
<img src="/illustrations/question-answered.svg" class="mt-4 mx-auto" style="max-height: 130px;">
</div>
<div>
<img src="/images/diagrammes_techniques_api_sequence_autorisation.png" class="w-full rounded">
</div>
</div>

<!--
- FastAPI choisi pour la génération automatique de la spécification OpenAPI
- LE point clé : pas rejeté, silencieusement ramené à son périmètre — donner l'exemple du diagramme (FreshMarket → NordDrive)
- Dire "vérifié en conditions réelles", pas juste "prévu en théorie"
-->

---
layout: default
---

# C12 — Documentation interactive (Swagger)

<div class="flex justify-center mt-4">
<img src="/images/swagger_omega_data_api.png" class="rounded border border-gray-300" style="max-height: 450px; width: auto;">
</div>

<div class="mt-2 text-xs text-center opacity-60"><code>localhost:8000/docs</code> — spécification OpenAPI générée automatiquement par FastAPI, testable directement dans le navigateur</div>

<!--
- Montrer l'URL à l'écran : localhost:8000/docs
- Dire que c'est généré automatiquement par FastAPI, pas écrit/maintenu à la main
- Si le temps le permet : ouvrir un endpoint en direct pour montrer l'auto-génération
-->

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

<div class="grid grid-cols-[62%_38%] gap-4 items-center mt-10">
<div class="text-sm">
Rapprochement <b>cohérent sur le jeu de données actuel</b>, mais
<b>non garanti par une contrainte formelle</b> — pas de clé étrangère
possible entre deux libellés texte de systèmes sources distincts.
Signalé explicitement pour traitement lors de la modélisation de
l'entrepôt (Bloc 3).
</div>
<img src="/illustrations/connection.svg" class="w-full">
</div>

<!--
- Présenter comme une transition honnête vers le Bloc 3, pas une faiblesse cachée
- Lire l'exemple concret affiché à voix haute : "NordDrive SARL" vs "NordDrive"
- Dire explicitement : signalé AVANT d'être découvert par quelqu'un d'autre
-->

---
layout: section
---

# Bloc 3 — Entrepôt OMEGA BI
## C13-C17 — ~15-20' (avec temps d'échange)

<img src="/illustrations/database-tables.svg" class="mx-auto mt-6 h-40">

<!--
- Transition : "Bloc 3, l'entrepôt OMEGA BI — 5 compétences, avec un temps d'échange dédié après C17"
- Prévenir le jury du temps d'échange à venir, pas une surprise
-->

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

<div class="grid grid-cols-[62%_38%] gap-4 items-center mt-6">
<div class="p-4 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
Inversion volontaire par rapport au Gantt initial : la purge RGPD (C16)
ne peut porter que sur un schéma <b>déjà historisé</b> — il faut donc que
C17 l'ait créé avant.
</div>
<img src="/illustrations/version-control.svg" class="w-full">
</div>

<!--
- Expliquer l'inversion C16/C17 par rapport au Gantt initial
- Raison simple : la purge RGPD (C16) a besoin du schéma déjà historisé, donc C17 doit passer avant
-->

---
layout: default
---

# C13 — Modéliser l'entrepôt

<div class="grid grid-cols-[40%_60%] gap-6 items-center mt-4">
<div>
<p class="text-sm">Approche bottom-up Kimball : <b>2 datamarts, 3 faits, 6 dimensions conformées</b></p>
<div class="flex flex-col gap-1 mt-2">
<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-700" style="width:fit-content"><b>Exploitation</b> — Fait_Expedition, Fait_Stock</span>
<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-orange-500/10" style="width:fit-content; color:#d9480f"><b>Commercial</b> — Fait_Commande</span>
</div>
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

<!--
- Kimball bottom-up, par datamart — pas un modèle monolithique unique
- Citer les 2 datamarts explicitement : Exploitation (expédition + stock) et Commercial (commande)
- LE point à expliquer : pourquoi pas de Fait_Livraison séparée — cardinalité 1:1 vérifiée empiriquement sur 1100 expéditions
-->

---
layout: default
---

# C13 — Méthode Kimball (bottom-up)

<p class="text-xs opacity-60"><code>modelisation_omega_bi.md</code> §1 — chaque datamart est livrable et utile seul, l'ensemble converge vers un entrepôt cohérent</p>

<div class="mt-5">
<div class="flex items-center gap-2 text-xs text-center">
<div class="p-2 rounded border-2 border-blue-500/40 bg-blue-500/5" style="width:150px">OLTP<br/><span class="opacity-70">FluxPro, TransFlow</span></div>
<div style="flex:1; border-top: 3px solid #1c7ed6; position:relative;"><span style="position:absolute; right:-9px; top:-7px; width:0; height:0; border-top:7px solid transparent; border-bottom:7px solid transparent; border-left:9px solid #1c7ed6;"></span></div>
<div class="p-2 rounded border-2 border-blue-500/40 bg-blue-500/5" style="width:120px">ETL<br/><span class="opacity-70">pipelines C15</span></div>
<div style="flex:1; border-top: 3px solid #1c7ed6; position:relative;"><span style="position:absolute; right:-9px; top:-7px; width:0; height:0; border-top:7px solid transparent; border-bottom:7px solid transparent; border-left:9px solid #1c7ed6;"></span></div>
<div class="p-2 rounded border-2 border-blue-500/40 bg-blue-500/5" style="width:160px">Datamarts<br/><span class="opacity-70">Exploitation, Commercial</span></div>
<div style="flex:1; border-top: 3px solid #1c7ed6; position:relative;"><span style="position:absolute; right:-9px; top:-7px; width:0; height:0; border-top:7px solid transparent; border-bottom:7px solid transparent; border-left:9px solid #1c7ed6;"></span></div>
<div class="p-2 rounded border-2 border-blue-500/50 bg-blue-500/10 font-bold" style="width:140px">Entrepôt<br/>OMEGA BI</div>
</div>
<div class="flex items-center gap-2 text-xs text-center mt-3">
<div class="p-2 rounded border-2 border-gray-400/40 opacity-70" style="width:150px">Capteurs IoT<br/><span class="opacity-70">batch + streaming</span></div>
<div style="flex:1; border-top: 3px dashed #adb5bd; position:relative;"><span style="position:absolute; right:-9px; top:-7px; width:0; height:0; border-top:7px solid transparent; border-bottom:7px solid transparent; border-left:9px solid #adb5bd;"></span></div>
<div class="p-2 rounded border-2 border-gray-400/40 opacity-70 font-bold" style="width:430px">Data Lake OMEGA LAKE — zones raw / staging / curated</div>
</div>
<div class="text-xs opacity-50 mt-1">Deux pipelines distincts : le data lake ne descend pas de l'entrepôt (sources, zones et finalité différentes — bloc 4)</div>
</div>

<div class="mt-5 p-3 rounded bg-orange-500/5 border border-orange-500/30">
<p class="text-xs font-bold uppercase tracking-wide opacity-70 mb-2">Exemple bottom-up : du besoin métier au datamart</p>
<div class="flex items-center gap-2 text-xs text-center">
<div class="p-2 rounded border border-orange-500/40" style="width:280px">Question métier (Direction des Opérations)<br/><span class="opacity-80">« Quel taux de service par client ? »</span></div>
<div class="text-sm opacity-40">→</div>
<div class="p-2 rounded border border-orange-500/40" style="width:260px">Requête BI formulée<br/><span class="opacity-80"><code>Fait_Expedition ⋈ Dim_Client ⋈ Dim_Temps</code></span></div>
<div class="text-sm opacity-40">→</div>
<div class="p-2 rounded border border-orange-500/50 bg-orange-500/10" style="width:220px">Datamart construit<br/><span class="opacity-80">Exploitation, <code>Dim_Client</code> conformée</span></div>
</div>
</div>

<!--
- Bottom-up Kimball : on ne part pas d'un modèle décisionnel monolithique, on part du besoin métier et on construit datamart par datamart
- Le schéma du haut distingue bien les deux pipelines : entrepôt (OLTP→ETL→datamarts) et data lake (IoT→zones) ne sont PAS la même chaîne
- L'exemple du bas est le même que celui déjà cité en C14/synthèse : taux de service par client — dimension conformée Dim_Client réutilisée entre Exploitation et Commercial
-->

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

<!--
- 5 schémas dans la même base Postgres que le staging — sobriété, pas un second conteneur
- Anecdote utile si le jury demande une difficulté rencontrée : bug Alembic (include_schemas=True manquant), trouvé seulement à la 2e migration
-->

---
layout: default
---

# C15 — Développer des pipelines de données

<div class="grid grid-cols-[55%_45%] gap-6 items-center mt-2">
<div>
<p class="text-sm">Pipeline ETL staging → entrepôt (<code>load_warehouse.py</code>)</p>
<ul class="text-sm mt-2 space-y-2">
<li>6 dimensions puis 3 faits, <b>une transaction unique</b> — rechargement complet à chaque exécution, sauf <code>Dim_Client</code> (historisée SCD2, jamais tronquée)</li>
<li>Contrôles qualité réels : mise en <b>quarantaine</b> des lignes non rapprochées</li>
<li>Cohérence vérifiée par <b>double calcul indépendant</b> : ETL (C15) et API (C12) partent de la <b>même base de staging</b> (C11) — deux chemins de calcul distincts, même résultat</li>
</ul>
</div>
<img src="/illustrations/filter.svg" class="w-full">
</div>

<!--
- 6 dimensions puis 3 faits, dans une transaction unique
- Rechargement complet à CHAQUE exécution, sauf Dim_Client (SCD2, jamais tronquée) — lien direct avec C17 à venir
- Double calcul indépendant ETL vs API : preuve de cohérence vérifiée, pas juste une affirmation
-->

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

<div class="flex items-center justify-center gap-2 mt-4 text-xs">
<div class="flex flex-col items-center gap-1"><img src="/icons/calendar-time.svg" class="h-9"><span>cron<br/>02h/03h</span></div>
<span class="opacity-30 text-lg">→</span>
<div class="flex flex-col items-center gap-1"><img src="/icons/database-blue.svg" class="h-9"><span><code>pg_dump</code></span></div>
<span class="opacity-30 text-lg">→</span>
<div class="flex flex-col items-center gap-1"><img src="/icons/archive.svg" class="h-9"><span><code>backups/</code></span></div>
<span class="opacity-30 text-lg">+</span>
<div class="flex flex-col items-center gap-1"><img src="/icons/clipboard-list.svg" class="h-9"><span>journal_<br/>operations</span></div>
</div>

<div class="mt-3 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
Périmètre étendu après clôture initiale : vues SQL + notebook jugés
insuffisants comme preuve de restitution → jalon transverse M4.
</div>

<!--
- Backup partiel quotidien (dim_client seule) / complet hebdomadaire (toute la base), déclenché par cron
- Pourquoi le mode partiel suffit : 7 des 8 tables sont reconstructibles depuis le staging, seule Dim_Client (historisée) ne l'est pas
- Journalisation sur une connexion séparée — survit à un ROLLBACK, bon point technique si la question se pose
-->

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

<div class="grid grid-cols-[55%_45%] gap-4 items-center mt-2">
<div class="text-sm">
<code>Dim_Client</code> historisée en <b>SCD2</b> : un changement de <code>nom</code>/<code>secteur</code> ferme
la version courante et en ouvre une nouvelle — jamais d'écrasement.
</div>
<div class="flex items-center justify-center gap-2 text-xs">
<span>Donnée source</span>
<span class="opacity-30">→</span>
<div class="flex flex-col items-center gap-1"><img src="/icons/git-branch.svg" class="h-8"><span>changement<br/>détecté</span></div>
<span class="opacity-30">→</span>
<span>ferme v42<br/>+ ouvre v87</span>
</div>
</div>

<div class="mt-3 text-xs overflow-x-auto">

| client_key | nom | secteur | valid_from | valid_to | is_current |
|---|---|---|---|---|---|
| 42 | NordDrive SARL | Automobile | 2026-01-01 | **2026-06-14** | **false** |
| **87** | **NordDrive Group** | **Automobile** | **2026-06-15** | — | **true** |

</div>
<div class="text-xs opacity-60 mt-1">Changement de <code>nom</code> le 15/06 → ligne 42 close, ligne 87 ouverte ; les faits déjà chargés avant cette date référencent toujours <code>client_key=42</code></div>

<!--
- Résumer le code affiché en 3 mots : comparer, fermer, ouvrir — pas besoin de le lire ligne par ligne
- Donner l'exemple du tableau à voix haute : NordDrive SARL (close 14/06) → NordDrive Group (ouverte 15/06)
- Point clé : les faits déjà chargés gardent la clé historique — pas de réécriture silencieuse de l'historique analytique
-->

---
layout: center
class: text-center
---

# Temps d'échange — Bloc 3

Questions du jury sur la modélisation / l'entrepôt

<div class="opacity-70 mt-4">(calibré sur E6, échange questions-réponses — pas une présentation continue)</div>

<!--
- S'arrêter vraiment ici, ne pas enchaîner automatiquement sur la suite
- Attendre les questions du jury avant de reprendre
- Si silence : proposer un angle (ex. "voulez-vous revenir sur la modélisation ou sur SCD2 ?")
-->

---
layout: section
---

# Bloc 4 — Data Lake OMEGA LAKE
## C18-C21 — ~10'

<img src="/illustrations/secure-server.svg" class="mx-auto mt-6 h-40">

<!--
- Transition rapide : "Bloc 4, le data lake OMEGA LAKE — 4 compétences, le plus technique"
- Annoncer que c'est le dernier bloc avant les jalons transverses
-->

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

<div class="mt-8 flex justify-center">
<img src="/images/architecture_omega_lake_trois_couches.png" class="rounded" style="width: 108%; max-width: 108%; margin-left: -4%;">
</div>

<!--
- Bien distinguer schema-on-write (staging/entrepôt) vs schema-on-read (lake)
- Si question "vous copiez quand même les données ?" : oui, raw/ est une copie fidèle octet pour octet — le schema-on-read porte sur l'interprétation de la structure, pas sur la copie elle-même
- Flux IoT jamais par le staging relationnel — flux d'ingestion séparé
-->

---
layout: default
---

# C18 — Zones raw / staging / curated

<div class="grid grid-cols-[20%_80%] gap-4 items-center mt-4">
<div class="text-xs">
<p><code>architecture_omega_lake.md</code></p>
<p class="mt-2">Clés naturelles de jointure vérifiées dans les données, jamais supposées.</p>
</div>
<div class="flex justify-center">
<img src="/images/architecture_omega_lake_zones.png" class="rounded" style="max-height: 480px; width: auto; max-width: 100%;">
</div>
</div>

<!--
- Zones raw / staging / curated — bien les nommer dans l'ordre
- Point clé : clés naturelles de jointure vérifiées dans les données réelles, jamais supposées à l'avance
-->

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

<!--
- 3 outils, 3 rôles différents — ne pas les confondre : MinIO = stockage, DuckDB = jointures, boto3 = copie fidèle
- Argument complet "pourquoi pas pandas" : charge tout en mémoire avant de joindre + dépendance jamais utilisée ailleurs dans le projet
- Anecdote concrète si "comment vérifié ?" : test kill -9 du consommateur SSE en cours de réception, puis redémarrage — aucune collision
-->

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

<!--
- Montrer la vraie console en direct si le temps/la connexion le permet, sinon la capture suffit
- 4 zones visibles comme de vrais préfixes S3 — pas une maquette, l'infrastructure réelle
-->

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

<!--
- Généré par introspection réelle, jamais maintenu à la main — même principe que l'audit RGPD de C16
- Si besoin d'une preuve concrète : montrer l'exemple JSON affiché, c'est une vraie sortie du programme
- Périmètre élargi à staging/curated, pas seulement raw/ — un catalogue réellement exploitable (schéma, volumétrie, fraîcheur)
-->

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
<div class="opacity-50"><img src="/icons/key.svg" class="h-6 mx-auto">+ clé secrète →</div>
<div class="p-2 rounded border border-blue-500/40 bg-blue-500/5">HMAC-SHA256</div>
<div class="opacity-50">→</div>
<div class="p-2 rounded border border-green-500/40 bg-green-500/5"><img src="/icons/eye-off.svg" class="h-5 mx-auto mb-1"><code>curated_bi/</code><br/>"a3f9...e21c"</div>
</div>
<div class="text-xs text-center opacity-60 mt-1"><img src="/icons/shield.svg" class="h-4 inline mr-1" style="vertical-align: -3px;"><code>curated/</code> (original) reste inaccessible au rôle <code>lake_reader</code>, qui ne voit que <code>curated_bi/</code> (pseudonymisé)</div>

1. Risque identifié dès C18 (recoupement géoloc ↔ chauffeur)
2. Première analyse incomplète — écartée, puis **réintroduite** après vérification approfondie
3. HMAC implémenté — hash simple = recalculable par force brute sur 15 véhicules
4. Repli codé en dur trouvé lors d'un **second contrôle** → garde-fou `verifier_cle_configuree()`
5. Risque résiduel assumé (stabilité de la clé entre exécutions) — documenté, pas masqué

<!--
- C'est le récit le plus riche de la présentation — prendre le temps, ne pas le précipiter
- Dérouler les 5 étapes dans l'ordre affiché, sans en sauter une
- Bien insister sur l'étape 2 (première analyse incomplète, réintroduite après vérification) — montre la rigueur de la démarche, pas une erreur à minimiser
- HMAC vs hash simple : expliquer pourquoi (15 véhicules seulement → recalculable par force brute sans clé)
- Étape 4 (repli codé en dur trouvé) : bon exemple concret si le jury demande "une difficulté rencontrée"
-->

---
layout: section
---

# M4 — Restitution BI (Grafana)
## + synthèse transverse + conclusion — ~10-15'

<img src="/illustrations/growth-analytics.svg" class="mx-auto mt-6 h-40">

<!--
- Transition : "jalon transverse M4, pas un bloc de compétences — ajouté en cours de programme"
- Annoncer qu'on enchaîne aussi la synthèse transverse et la conclusion dans ce même temps
-->

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

<!--
- Ne pas laisser penser que le monitoring initial était un échec — c'est un écart de forme, pas de fond
- Notebook = preuve exploratoire gardée telle quelle ; vues SQL = KPIs déjà corrects et interrogeables
- Grafana = complément, pas un remplacement — décidé avant Power BI/Databricks pour rester 100 % local
-->

---
layout: default
---

# Infrastructure : un seul `docker-compose.yml`

<div class="flex items-center gap-2 mb-3">
<img src="/logos/docker.svg" class="h-6">
<code class="text-sm">docker compose -f infra/docker/docker-compose.yml --env-file .env up -d</code>
</div>

<div class="flex flex-col gap-1 mt-2 text-sm">
<div class="flex items-center gap-3 p-2 rounded border-b border-gray-400/20">
<img src="/logos/postgresql.svg" class="h-7" style="width:28px;">
<div style="width: 260px;">PostgreSQL (staging + entrepôt)</div>
<div style="width: 60px;" class="opacity-70">5432</div>
<code class="text-xs">psql ou client SQL</code>
</div>
<div class="flex items-center gap-3 p-2 rounded border-b border-gray-400/20">
<div class="rounded-full flex items-center justify-center flex-shrink-0" style="width:28px; height:28px; background:#1c7ed6;"><img src="/icons/engine.svg" style="width:16px; height:16px;"></div>
<div style="width: 260px;">api-mock (FluxPro / TransFlow / portail / capteurs)</div>
<div style="width: 60px;" class="opacity-70">5050</div>
<code class="text-xs">localhost:5050/portail-transporteur/colis</code>
</div>
<div class="flex items-center gap-3 p-2 rounded border-b border-gray-400/20">
<img src="/logos/fastapi.svg" class="h-7" style="width:28px;">
<div style="width: 260px;">API Omega Data (FastAPI)</div>
<div style="width: 60px;" class="opacity-70">8000</div>
<code class="text-xs">localhost:8000/docs</code>
</div>
<div class="flex items-center gap-3 p-2 rounded border-b border-gray-400/20">
<img src="/logos/minio.svg" class="h-7" style="width:28px;">
<div style="width: 260px;">MinIO (console web)</div>
<div style="width: 60px;" class="opacity-70">9001</div>
<code class="text-xs">localhost:9001</code>
</div>
<div class="flex items-center gap-3 p-2 rounded border-b border-gray-400/20">
<img src="/logos/grafana.svg" class="h-7" style="width:28px;">
<div style="width: 260px;">Grafana</div>
<div style="width: 60px;" class="opacity-70">3000</div>
<code class="text-xs">localhost:3000</code>
</div>
<div class="flex items-center gap-3 p-2 rounded">
<img src="/icons/mail.svg" class="h-7" style="width:28px;">
<div style="width: 260px;">MailHog (boîte des alertes)</div>
<div style="width: 60px;" class="opacity-70">8025</div>
<code class="text-xs">localhost:8025</code>
</div>
</div>

<div class="mt-4 text-sm opacity-70">
Auto-hébergé, sans dépendance à un service cloud — cohérent avec la
sobriété numérique (RGESN) retenue dès C3. Mots de passe injectés via
<code>--env-file .env</code>, jamais codés en dur.
</div>

<!--
- Un seul docker-compose.yml, tout auto-hébergé — pas de service cloud payant
- Mots de passe injectés via .env, jamais codés en dur — bon réflexe sécurité à mentionner si demandé
-->

---
layout: default
---

# C16bis — Restitution OMEGA BI

<div class="grid grid-cols-[42%_58%] gap-6 items-center mt-4">
<div>
<p class="text-sm">Dashboard Grafana connecté en lecture seule (<code>bi_reader</code>)</p>
<ul class="text-sm mt-3 space-y-2">
<li>Taux de service par client : <b>FreshMarket 90,6 %</b>, <b>NordDrive 87,5 %</b>, <b>MedioTex 87,3 %</b></li>
<li>Délai moyen de livraison par transporteur : <b>2,0 j</b> (RapidFret) à <b>2,4 j</b> (EcoRoute)</li>
<li>Stock disponible par entrepôt : <b>11 190</b> (Lyon) à <b>13 757</b> (Marseille) unités, 30 références chacun</li>
</ul>
</div>
<div>
<img src="/images/gestion_operationnelle_omega_bi_dashboard_grafana.png" class="w-full rounded">
</div>
</div>

<!--
- Montrer le dashboard, citer les 3 chiffres affichés (taux de service, délai moyen, stock disponible)
- bi_reader = rôle lecture seule, pas d'accès en écriture au dashboard
-->

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

<!--
- Point technique important si demandé : verifier_sante_infrastructure() ne lève jamais d'exception — l'échec EST le résultat à enregistrer, pas un bug à cacher
- Raconter le test réel dans l'ordre : coupure MinIO → relevé en échec → alerte Grafana active en ~30s → e-mail reçu dans MailHog → remise en service → alerte résolue
-->

---
layout: default
---

# Limite assumée : granularité réelle du monitorage

<div class="flex flex-col gap-3 mt-4">
<div class="flex items-center gap-4 p-3 rounded border border-gray-400/30">
<img src="/illustrations/server-status.svg" style="height: 70px; width: auto;" class="flex-shrink-0">
<div class="text-sm font-bold" style="width: 190px;">SSE capteurs<br/><code class="text-xs font-normal">flux_sse_capteurs</code></div>
<div class="flex gap-2 flex-wrap">
<span class="inline-flex items-center gap-1 text-sm px-2 py-1 rounded-full bg-green-500/15 text-green-700"><b>✓</b> Fraîcheur/volumétrie</span>
<span class="inline-flex items-center gap-1 text-sm px-2 py-1 rounded-full bg-red-500/10" style="color:#c92a2a"><b>✕</b> Débit / latence / déconnexion</span>
</div>
</div>
<div class="flex items-center gap-4 p-3 rounded border border-gray-400/30">
<img src="/illustrations/web-search.svg" style="height: 70px; width: auto;" class="flex-shrink-0">
<div class="text-sm font-bold" style="width: 190px;">Scraping portail transporteur</div>
<div class="flex gap-2 flex-wrap">
<span class="inline-flex items-center gap-1 text-sm px-2 py-1 rounded-full bg-red-500/10" style="color:#c92a2a"><b>✕</b> Aucun suivi persisté — <code class="text-xs">print()</code> console uniquement</span>
</div>
</div>
</div>

<div class="mt-6 text-sm opacity-70">
Le monitorage (<code>monitoring</code>, C20bis) a été construit
spécifiquement pour C20 (data lake, Bloc 4) — le Bloc 2 n'a jamais eu
d'équivalent. Documenté au chapitre 6 du rapport, suivi par l'issue #104
(backlog, à traiter si le temps le permet).
</div>

<!--
- Assumer directement, ne pas attendre la question : SSE partiellement suivi, scraping pas du tout
- Expliquer pourquoi : le monitorage a été construit spécifiquement pour C20 (Bloc 4), jamais étendu au Bloc 2
- Mentionner l'issue #104 (backlog) — montre que c'est tracé et assumé, pas oublié
-->

---
layout: default
---

# Synthèse transverse — Budget cumulé

<div class="flex flex-col gap-2 mt-6 text-sm">
<div class="flex items-center gap-3">
<div style="width: 260px;">Phase 1 — Cadrage (M0)</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6 relative"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:45%; background:#1c7ed6;">25 000 €</div></div>
<span class="inline-flex items-center gap-1 text-xs text-green-700" style="width:110px;"><b>✓</b> Consommé</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 260px;">Phase 2 — Collecte & Stockage (M1)</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6 relative"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:82%; background:#1c7ed6;">45 000 €</div></div>
<span class="inline-flex items-center gap-1 text-xs text-green-700" style="width:110px;"><b>✓</b> Consommé</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 260px;">Phase 3 — Entrepôt OMEGA BI (M2)</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6 relative"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:100%; background:#1c7ed6;">55 000 €</div></div>
<span class="inline-flex items-center gap-1 text-xs text-green-700" style="width:110px;"><b>✓</b> Consommé</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 260px;">Phase 4 — Data Lake OMEGA LAKE (M3)</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6 relative"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:100%; background:#1c7ed6;">55 000 €</div></div>
<span class="inline-flex items-center gap-1 text-xs text-green-700" style="width:110px;"><b>✓</b> Consommé</span>
</div>
<div class="flex items-center gap-3 mt-2 pt-2 border-t-2 border-gray-400/30 font-bold">
<div style="width: 260px;">Total</div>
<div class="flex-1 text-lg">180 000 €</div>
<span class="inline-flex items-center gap-1 text-xs text-green-700" style="width:110px;">Aucun dépassement</span>
</div>
</div>

<div class="mt-4 text-sm opacity-70">
Jalons transverses (M4, M5, M6) : staffing interne uniquement, outils
open source auto-hébergés — jamais de ligne budgétaire propre.
</div>

<!--
- Lire le total : 180 000 €, aucun dépassement sur l'ensemble du programme
- Préciser que M4/M5/M6 (jalons transverses) n'ont jamais eu de ligne budgétaire propre — staffing interne, outils open source
-->

---
layout: default
---

# Synthèse transverse — Qualité : évolution des tests

<div class="flex flex-col gap-2 mt-6 text-sm">
<div class="flex items-center gap-3">
<div style="width: 190px;">M0 — Cadrage & Setup</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:7%; background:#0ca678;">13</div></div>
<span class="text-xs opacity-60" style="width:70px;">—</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 190px;">M1 — Collecte & Stockage</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:38%; background:#0ca678;">67</div></div>
<span class="text-xs text-green-700" style="width:70px;">▲ ×5,2</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 190px;">M2 — Entrepôt OMEGA BI</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:55%; background:#0ca678;">96</div></div>
<span class="text-xs text-green-700" style="width:70px;">▲ +43 %</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 190px;">M3 — Data Lake OMEGA LAKE</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:82%; background:#0ca678;">143</div></div>
<span class="text-xs text-green-700" style="width:70px;">▲ +49 %</span>
</div>
<div class="flex items-center gap-3">
<div style="width: 190px;">M4 — Restitution BI</div>
<div class="flex-1 bg-gray-400/10 rounded-full h-6"><div class="h-6 rounded-full flex items-center justify-end pr-2 text-white text-xs font-bold" style="width:100%; background:#0ca678;">174</div></div>
<span class="text-xs text-green-700" style="width:70px;">▲ +22 %</span>
</div>
</div>
<div class="text-xs opacity-60 mt-1">174 fonctions de test (176 cas <code>pytest</code>, voir chapitre 1 du rapport)</div>

<div class="mt-4 text-sm opacity-70">
Croissance non linéaire avec le volume de code : les blocs 2 et 3
ajoutent proportionnellement plus de tests, cohérent avec une suite qui
couvre systématiquement les cas limites.
</div>

<!--
- 174 fonctions de test (176 cas pytest une fois les tests paramétrés comptés) — expliquer la nuance seulement si demandé
- Croissance pas linéaire : blocs 2 et 3 ajoutent proportionnellement plus de tests, cohérent avec une couverture des cas limites
-->

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

<!--
- LE message à faire passer : contrôle qualité à chaque étape, pas un audit ponctuel en fin de programme
- RGPD : renvoyer en une phrase au parcours pseudonymisation déjà vu en C21, ne pas tout redérouler
- RGESN : citer 2-3 exemples déjà vus (pas de big data séparé, pas d'orchestrateur, outils auto-hébergés)
-->

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

<!--
- Revenir sur les 5 objectifs, insister sur "pas tous du premier coup" — honnêteté assumée, pas une excuse
- Objectif 3 (tableau de bord) = le seul avec un détour (vues SQL/notebook → Grafana M4) — le redire une dernière fois ici
-->

---
layout: default
---

# Limites connues

<div class="text-sm" style="columns: 2; column-gap: 24px;">
<ul class="space-y-1" style="list-style-position: outside;">
<li style="break-inside: avoid;"><b>Aucune interaction réelle avec un système tiers externe</b> — toutes les sources sont simulées par <code>api-mock</code></li>
<li style="break-inside: avoid;">Rapprochement <code>clients.nom</code> ↔ <code>historique_expeditions.client</code> non garanti par contrainte formelle</li>
<li style="break-inside: avoid;">Aucun ordonnanceur actif (sauvegardes, purge RGPD) — exécution manuelle/cron</li>
<li style="break-inside: avoid;">Stabilité de la clé de pseudonymisation entre exécutions non surveillée</li>
<li style="break-inside: avoid;">Prestataire SupervIT jamais mobilisé — écart assumé</li>
<li style="break-inside: avoid;">Observabilité partielle par choix (pas de Loki/ELK, pas de tracing)</li>
</ul>
</div>

<div class="flex items-center gap-3 mt-6">
<div class="p-2 rounded border-2 border-green-500/50 text-xs text-center" style="width:200px">
<code>api-mock</code><br/><span class="opacity-70">FluxPro, TransFlow, portail, capteurs</span>
</div>
<div style="flex:1; border-top: 3px solid #2f9e44; position:relative;">
<span style="position:absolute; right:-10px; top:-7px; width:0; height:0; border-top:7px solid transparent; border-bottom:7px solid transparent; border-left:10px solid #2f9e44;"></span>
</div>
<div class="p-2 rounded border-2 border-green-500/50 bg-green-500/5 text-xs text-center font-bold" style="width:140px">Pipeline<br/>DATA CORE</div>
<span class="text-xs text-green-700 ml-1">câblé, testé</span>
</div>
<div class="flex items-center gap-3 mt-2">
<div class="p-2 rounded border-2 border-gray-400/40 text-xs text-center opacity-60" style="width:200px">
Systèmes réels<br/><span class="opacity-70">ERP, TMS, portail, capteurs physiques</span>
</div>
<div style="flex:1; border-top: 3px dashed #adb5bd; position:relative;">
<span style="position:absolute; right:-10px; top:-7px; width:0; height:0; border-top:7px solid transparent; border-bottom:7px solid transparent; border-left:10px solid #adb5bd;"></span>
</div>
<div class="p-2 rounded border-2 border-gray-400/40 text-xs text-center opacity-60" style="width:140px">Pipeline<br/>DATA CORE</div>
<span class="text-xs opacity-50 ml-1">jamais connecté</span>
</div>
<div class="text-xs text-center opacity-60 mt-2">Même interface des deux côtés — reconfigurer <code>*_API_URL</code>/<code>API_KEY</code> suffirait, rien n'est codé en dur</div>

<!--
- Ne pas minimiser : lire les limites clairement, avec un ton assumé plutôt que gêné
- Le schéma câblé/pas câblé résume tout : même interface des deux côtés, question de configuration, pas de code à réécrire
-->

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
- 3 apprentissages, dans l'ordre affiché : décider avant de coder, vérifier empiriquement, contrôle qualité à plusieurs niveaux
- Ne PAS écrire "assistance IA" sur la slide (décision du 22/10/2026)
- Si la question de l'IA est posée par le jury, le dire oralement ici : chaque décision structurante a été arbitrée et validée par le Data Engineer, jamais déléguée — historique Git public disponible si besoin de preuve
-->

---
layout: center
class: text-center
---

# Questions & échanges avec le jury

<div class="opacity-70 mt-4">~10' — ouvert à tous les blocs</div>

<!--
- Rester silencieux, laisser le jury prendre la parole en premier
- Se relire mentalement synthese_technique_oral.md avant la soutenance, pas pendant
-->

---
layout: end
---

<img src="/illustrations/handshake-deal.svg" class="mx-auto h-40">

# Merci

<div class="opacity-70">
Dépôt public : github.com/alaugier/datacore
</div>

<!--
- Remercier le jury pour son temps et son attention
- Rappeler que le dépôt est public, consultable après la soutenance
- Rester disponible pour des questions complémentaires même après la clôture officielle
-->
