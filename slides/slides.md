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
layout: image-right
backgroundSize: contain
image: /illustrations/logistics.svg
---

# Contexte — Omega Logistics

Prestataire logistique (3PL), 3 sites : **Lyon, Lille, Marseille**

<div class="grid grid-cols-1 gap-2 mt-6">
<div class="flex items-center gap-3 p-2 rounded border border-gray-400/30">
<div class="w-2 h-8 rounded bg-blue-500 flex-shrink-0"></div>
<div class="text-sm"><b>NordDrive</b> — pièces automobiles, flux tendus</div>
</div>
<div class="flex items-center gap-3 p-2 rounded border border-gray-400/30">
<div class="w-2 h-8 rounded bg-green-500 flex-shrink-0"></div>
<div class="text-sm"><b>FreshMarket</b> — grande distribution alimentaire, température & traçabilité</div>
</div>
<div class="flex items-center gap-3 p-2 rounded border border-gray-400/30">
<div class="w-2 h-8 rounded bg-orange-500 flex-shrink-0"></div>
<div class="text-sm"><b>MedioTex</b> — textile, forte saisonnalité</div>
</div>
</div>

<div class="mt-6 text-sm">
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

<img src="/illustrations/meeting.svg" class="mx-auto mt-6 h-40">

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

<img src="/illustrations/delivery-truck.svg" class="mx-auto mt-6 h-40">

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
layout: default
---

# C8 — Automatiser l'extraction

<div class="text-sm">
5 connecteurs, 31 tests : API REST (TransFlow) · Scraping du portail
transporteur · Requêtes SQL directes (FluxPro) · Fichiers clients
hétérogènes · Historique volumineux
</div>

<div class="mt-4">
<img src="/images/diagrammes_techniques_ingestion_c8.png" class="w-full rounded">
</div>

<div class="mt-2 text-sm opacity-70">→ Démo live à ce point (voir issue #98)</div>

---
layout: default
---

# C9 — Requêtes SQL d'extraction

`docs/architecture/requetes_sql_extraction.md` — 5 requêtes documentées avec leurs résultats réels

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
layout: default
---

# C11 — Créer une base de données

<div class="grid grid-cols-[40%_60%] gap-6 items-center mt-4">
<div>
<p class="text-sm">Méthode MERISE, versionnée via Alembic</p>
<ul class="text-sm mt-3 space-y-2">
<li>2 violations de formes normales trouvées <b>empiriquement</b>, corrigées</li>
<li>Clé de rapprochement <code>tracking_number</code> (livraisons ↔ expéditions), <b>sans FK formelle</b> — systèmes sources distincts</li>
</ul>
</div>
<div>
<img src="/images/modelisation_merise_mcd.png" class="w-full rounded">
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

<img src="/illustrations/data-processing.svg" class="mx-auto mt-6 h-40">

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

```bash
# scripts/backup_omega_bi.sh --partiel|--complet
trap journaliser_echec ERR   # enregistre l'échec AVANT la fin du script
pg_dump -U "$PG_USER" -d "$OMEGA_BI_DB" \
  --table=dimensions.dim_client > "$FICHIER"   # --partiel : la seule table non reconstructible
```

- Sauvegardes planifiées (partielle quotidienne / complète hebdomadaire) — 7 des 8 tables reconstructibles depuis le staging
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
<b>Schema-on-read</b>, pas schema-on-write (staging/entrepôt) — flux IoT en
ingestion directe, <b>jamais</b> par la base de staging relationnelle, la
zone <code>curated/</code> se joint à la lecture aux dimensions conformées de l'entrepôt.
</div>

<div class="mt-4">
<img src="/images/architecture_omega_lake_trois_couches.png" class="w-full rounded">
</div>

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

<div class="flex items-center gap-3 mb-2">
<img src="/logos/minio.svg" class="h-7">
<img src="/logos/duckdb.svg" class="h-7">
<span class="text-sm">MinIO (S3) + <b>DuckDB</b> (jointures) + <b>boto3</b> (copie fidèle de <code>raw/</code>)</span>
</div>

<div class="mt-3 p-3 rounded bg-blue-500/10 border border-blue-500/30 text-sm">
<b>Pourquoi pas pandas ?</b> Chargerait les tables entières en mémoire
avant de joindre, sans langage de requête (juste des appels d'API) — et
aurait introduit une dépendance que le projet n'utilise nulle part
ailleurs (vérifié par grep avant de choisir). DuckDB s'aligne avec
l'existant : requêtes SQL directes, comme le reste du projet interroge
déjà PostgreSQL.
</div>

<div class="mt-3 p-3 rounded bg-orange-500/10 border border-orange-500/30 text-sm">
DuckDB peut reformater silencieusement un CSV/JSON en le réécrivant —
incompatible avec la garantie « octet pour octet » de <code>raw/</code>
(vérifiée par somme de contrôle SHA-256). <code>boto3</code> transfère
des octets sans les interpréter.
</div>

<div class="mt-3 text-sm">
<b>Flux SSE</b> fenêtré par intervalle de 5 minutes, vérifié par <b>coupure
brutale réelle</b> (<code>kill -9</code> puis redémarrage) : aucune collision, aucune
donnée corrompue.
</div>

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

<img src="/illustrations/monitor.svg" class="mx-auto mt-6 h-40">

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

Grafana → service interne authentifié → `smtplib` → MailHog

<div class="mt-3 p-3 rounded bg-green-500/10 border border-green-500/30 text-sm">
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

- **RGPD** — la pseudonymisation (C21) : risque identifié → analyse
  incomplète écartée → réintroduite après vérification approfondie →
  faille (repli codé en dur) trouvée lors d'un second contrôle →
  risque résiduel assumé
- **RGESN** — critère invoqué à chaque choix d'infrastructure
  (pas de « big data » séparé, pas d'orchestrateur, outils auto-hébergés)
- **RGAA** — accessibilité appliquée en continu aux livrables
  Markdown/PDF, pas vérifiée une seule fois en fin de programme

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

<div class="mt-6 p-4 rounded bg-blue-500/10 border border-blue-500/30">
Programme mené avec l'assistance d'outils d'IA sous supervision humaine
constante — chaque décision structurante arbitrée et validée par le
Data Engineer, jamais déléguée. Historique Git public disponible.
</div>

<img src="/illustrations/team-collaboration.svg" class="mx-auto mt-4 h-28">

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
