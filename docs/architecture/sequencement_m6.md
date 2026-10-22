# Séquencement du milestone M6 — Présentation orale

Même principe que [`sequencement_bloc2.md`](sequencement_bloc2.md)/
[`sequencement_bloc3.md`](sequencement_bloc3.md)/
[`sequencement_bloc4.md`](sequencement_bloc4.md)/
[`sequencement_m5.md`](sequencement_m5.md) : décider l'ordre et le
découpage avant de produire du contenu, pas en cours de route. M6 n'est
pas un bloc de compétences RNCP — c'est le jalon transverse de
préparation à la soutenance orale. Structure élaborée avec l'assistance
d'un outil IA, arbitrée et validée par le Data Engineer / chef de
projet le 21/10/2026 — même méthodologie de travail que le reste du
programme (voir chapitre 00 du rapport).

---

## 1. Point de départ

Le programme (M0-M5) est fonctionnellement et documentairement complet
(`docs/comptes_rendus/M5.md` §5). M6 ne modifie **aucun** script ni
pipeline existant — déjà validés de bout en bout, en conditions
réelles, à chaque jalon précédent. M6 produit uniquement les supports
de la soutenance, listés en §1.1 ; la forme attendue par le jury pour
ces supports est précisée en §1.2.

### 1.1 Supports déjà disponibles, réutilisés pour M6

| Support déjà disponible | Réutilisation prévue pour M6 |
|---|---|
| `docs/latex/rapport.pdf` (37 pages) | Trame de la présentation (même séquence de blocs) |
| Diagrammes Mermaid déjà exportés en PNG (`docs/architecture/images/`, `docs/latex/figures/`) | Réutilisés tels quels dans les slides (export PNG, pas de redessin -- **aucun schéma n'est en TikZ dans ce projet**, tous sont Mermaid) |
| `docs/architecture/index_code_par_competence.md` | Base de l'anticipation Q&A jury sur le code |
| `docs/architecture/synthese_technique_oral.md` | Base de l'anticipation Q&A jury sur les écarts/limites |
| Chapitre 5 §6.5 du rapport (commandes de rejeu des pipelines) | Base du script de démo live |

### 1.2 Forme attendue par le jury

`docs/reference/[DE] Notes sur la certification.pdf` (copié dans le
dépôt le 22/10/2026) page 8 détaille un déroulé d'épreuve par bloc
(E1-E7), chacune avec un temps de passage oral distinct : E1 (5'),
E2 (20'), E3 (10') pour le Bloc 1 ; E4 (15') pour le Bloc 2 ; E5 (10'),
E6 (5-10') pour le Bloc 3 ; E7 (10') pour le Bloc 4 ; plus 10' de
questions/échanges transverses avec le jury à la fin. Ce même document
(pages 4-7) associe à chaque épreuve un livrable écrit distinct
(rapport de 5 à 20 pages selon l'épreuve).

**Décision actée le 22/10/2026** : ce livrable écrit séparé par
épreuve **n'est pas exigé** pour cette certification -- c'est l'oral
qui est jugé. Le rapport unique déjà produit en M5
(`docs/latex/rapport.pdf`, 37 pages) reste la base écrite du
programme, **non retravaillé** pour épouser ce découpage en 7
documents séparés : le temps restant avant la soutenance est mieux
investi dans la préparation de l'oral lui-même. En revanche, le
**minutage et le contenu attendu par épreuve** servent de boussole
pour calibrer la trame de présentation (livrable 2 ci-dessous) --
seule donnée fiable disponible sur le temps réellement alloué par
section. **À confirmer avec le formateur** : la durée totale réelle de
la soutenance et si elle se déroule en plusieurs temps distincts par
bloc ou en un passage continu -- n'a pas encore été vérifié, traité
comme hypothèse de travail par défaut en attendant.

## 2. Livrables attendus

| # | Livrable | S'appuie sur |
|---|---|---|
| 1 | Anticipation Q&A jury (enrichissement, pas une nouvelle base) | `index_code_par_competence.md`, `synthese_technique_oral.md` |
| 2 | Trame de présentation (slides) | `rapport.pdf`, diagrammes déjà exportés |
| 3 | Script de démo live, minuté | Chapitre 5 §6.5 du rapport (commandes de rejeu) |
| 4 | Checklist technique pré-soutenance (si Slidev retenu) | Outil retenu à l'issue du livrable 2 |
| 5 (optionnel, priorité basse) | DAG Airflow orchestrant les scripts existants, sans réécriture de logique métier | Scripts déjà validés (chapitre 5 §6.5) |

**Outil de présentation** : Slidev par défaut (Markdown, cohérent avec
le reste du projet versionné en texte), bascule vers PowerPoint si le
rendu d'un premier jet n'est pas jugé assez illustré/professionnel --
décision prise après ce premier jet, pas a priori.

**Minutage de la trame** (hypothèse de travail, §1.2) : le découpage
E1-E7 ne couvre explicitement que les 4 blocs RNCP, pas les jalons
transverses propres au programme (M4, synthèse transverse, conclusion)
-- calibrage proposé pour que la trame reste réaliste sur un total
d'environ 90-100 minutes :

| Section de la trame | Durée visée | Calibrée sur |
|---|---|---|
| Contexte Omega Logistics / DATA CORE | ~5' | (hors grille E1-E7, mise en contexte nécessaire) |
| Bloc 1 — Cadrage (C1-C7) | ~30-35' | E1+E2+E3 |
| Bloc 2 — Collecte & Stockage (C8-C12), avec démonstration | ~15' | E4 |
| Bloc 3 — Entrepôt OMEGA BI (C13-C17), avec temps d'échange dédié | ~15-20' | E5+E6 |
| Bloc 4 — Data Lake OMEGA LAKE (C18-C21) | ~10' | E7 |
| M4 (Grafana) + synthèse transverse + conclusion/perspectives | ~10-15' | (hors grille E1-E7, ajout propre au programme) |
| Questions & échanges avec le jury | ~10' | TOUS |

E6 est explicitement un **échange questions-réponses**, pas une
présentation continue -- à traiter comme tel dans la trame (prévoir un
temps d'arrêt/interaction sur le Bloc 3, pas un monologue jusqu'au
bout).

**Sur l'orchestrateur (Airflow)** : déjà tranché en M5 (chapitre 5 du
rapport, « Pourquoi pas un orchestrateur ») -- non exigé pour valider
la compétence, mais constitue un plus (confirmé par le formateur). Les
scripts/pipelines existants ne changent pas : un DAG Airflow, si du
temps reste après le cœur de M6, se contenterait d'appeler les CLI
déjà validées telles quelles (`python3 -m datacore.*`), sans aucune
réécriture de logique métier. Traité en dernier, en dernière
priorité : si le temps manque, la réponse orale déjà actée dans le
rapport suffit -- pas d'implémentation forcée sous contrainte de temps
à quelques jours de la soutenance.

## 3. Découpage en issues et ordre de rédaction

| Issue | Portée | Dépend de |
|---|---|---|
| 1 | Anticipation Q&A jury | Rien -- peut démarrer immédiatement, s'appuie sur du contenu déjà existant |
| 2 | Trame de présentation (slides) | Rien -- s'appuie sur le rapport déjà stable |
| 3 | Script de démo live, minuté | Issue 2 (la démo doit s'articuler avec la trame finale) |
| 4 | Checklist technique pré-soutenance | Issue 2 (dépend de l'outil retenu à l'issue du premier jet) |
| 5 (optionnelle, priorité basse) | DAG Airflow (stretch goal) | Issues 1-4 terminées, traitée seulement si le temps restant avant la soutenance le permet sans risque |

**Ordre retenu : Issue 1 → Issue 2 → (Issue 3, Issue 4 en parallèle) →
Issue 5 si le temps le permet.** L'anticipation Q&A (issue 1) est
indépendante et rapide (enrichissement de documents déjà existants) :
traitée en premier pour ne pas la sacrifier si le temps manque en fin
de jalon. La trame de présentation (issue 2) est le livrable central,
dont dépendent la démo (issue 3) et la checklist technique (issue 4).
L'orchestrateur (issue 5) reste strictement un stretch goal, non
engagé avant que le reste du jalon soit stable.
