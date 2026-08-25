# Supervision du programme DATA CORE

**Compétence couverte : C6 — Superviser la réalisation d'un projet data**
**Épreuves associées : E2 (mise en situation professionnelle), E3 (jeu de rôle)**

Ce document s'appuie sur la [feuille de route](feuille_de_route.md) (C5,
composition d'équipe et budget prévisionnel) et documente les rituels de
supervision du programme : points d'équipe hebdomadaires, comité de suivi
mensuel (CoSu), tableau de suivi budgétaire et modalités d'encadrement du
prestataire externe SupervIT.

---

## 1. Rituels d'équipe

### 1.1 Point d'équipe hebdomadaire

| Élément | Détail |
|---|---|
| Fréquence | Chaque lundi, 30 minutes |
| Participants | Data Engineer / chef·fe de projet (moi), Sophie MARTIN (Lead DE), Yanis DUPONT (DE), Léa FONTAINE (Data Analyst), Thomas NGUYEN (DevOps) |
| Ordre du jour type | 1) Avancement des issues en cours (statut Kanban) — 2) Blocages à lever — 3) Priorités de la semaine — 4) Points de veille technique/réglementaire à signaler (C4) |
| Format de compte-rendu | 5-10 lignes, archivées ci-dessous, diffusées à l'équipe le jour même |

**Exemple — compte-rendu du 17/08/2026.**
Avancement : cadrage (C1-C3) en cours, entretiens de cadrage réalisés.
Blocage : aucun. Priorité de la semaine : finaliser la topographie des
données et démarrer l'étude d'architecture cible. Veille signalée :
comparatif orchestrateurs ETL légers (cf.
[veille technique et réglementaire](veille_technique_reglementaire.md#semaine-du-17082026)).

**Exemple — compte-rendu du 24/08/2026.**
Avancement : C1 à C3 et C5 livrés et mergés sur `dev` ; conteneurisation
(docker-compose) testée de bout en bout. Blocage : aucun. Priorité de la
semaine : pipeline CI (C8 infra) puis bascule sur le bloc 2. Décision
d'équipe : extension du Kanban à 6 statuts pour un suivi plus fin des PR
en revue.

### 1.2 Comité de suivi mensuel (« CoSu »)

| Élément | Détail |
|---|---|
| Fréquence | Mensuelle, 1 heure, dernier jeudi du mois (ou à échéance de jalon) |
| Participants | Data Engineer / chef·fe de projet (moi), Karim BELAÏD (commanditaire opérationnel), Éléonore RAKOTO (sponsor) |
| Ordre du jour type | 1) Avancement du programme vs feuille de route — 2) Suivi budgétaire (§2) — 3) Risques et arbitrages nécessaires — 4) Décisions à valider par la sponsor |
| Format de compte-rendu | Structuré (voir exemple ci-dessous), archivé et communiqué aux deux parties prenantes |

**Exemple — CoSu du 25/08/2026 (premier comité, clôture de la phase de cadrage).**

- **Avancement** : Phase 1 (Cadrage & Setup, M0) quasiment terminée.
  Livrables C1 (étude de faisabilité), C2 (topographie des données), C3
  (architecture cible), C5 (feuille de route) et C4 (veille) livrés et
  validés. Infrastructure (docker-compose, CI) opérationnelle.
- **Décisions actées depuis le dernier point** : choix de MinIO plutôt que
  Microsoft Fabric pour le futur data lake (contrainte de fonctionnement
  local, coût, reproductibilité — voir
  [architecture cible §2.5](architecture_cible.md#25-alternative-écartée--microsoft-fabric)) ;
  extension du tableau Kanban de 3 à 6 statuts pour un suivi plus fin.
- **Point d'attention soulevé en comité** : lors de la rédaction du
  compte rendu de milestone, un écart a été identifié entre le suivi
  GitHub et le cahier des charges — les livrables C4, C6 et C7 n'avaient
  pas d'issue dédiée. Décision actée en comité : ouvrir les 3 issues
  manquantes avant de considérer M0 comme clos, plutôt que de basculer
  prématurément sur le bloc 2 (voir
  [compte rendu M0 §4](../comptes_rendus/M0.md#4-écarts-par-rapport-au-cahier-des-charges)).
- **Budget** : voir §2 ci-dessous, aucun dépassement à ce stade.
- **Risques** : aucun risque bloquant identifié pour le passage au bloc 2 ;
  point de vigilance sur la charge de travail liée au rattrapage C6/C7 en
  parallèle du démarrage du bloc 2.

---

## 2. Tableau de suivi budgétaire

Suivi du budget de la Phase 1 — Cadrage (25 000 €, cf.
[feuille de route §3](feuille_de_route.md#3-budget-prévisionnel)), ventilé
par poste de livrable. Situation au 25/08/2026.

| Poste | Budget prévisionnel | Réalisé à date | Écart | Statut |
|---|---|---|---|---|
| C1 — Étude de faisabilité | 2 500 € | 2 500 € | 0 € | Terminé |
| C2 — Topographie des données | 2 500 € | 2 500 € | 0 € | Terminé |
| C3 — Architecture cible | 3 000 € | 3 000 € | 0 € | Terminé |
| C4 — Veille technique et réglementaire | 2 000 € | 2 000 € | 0 € | Terminé |
| C5 — Feuille de route | 2 500 € | 2 500 € | 0 € | Terminé |
| C6 — Supervision (ce livrable) | 2 000 € | 1 000 € | 1 000 € | En cours |
| C7 — Communication et lancement | 2 500 € | 0 € | 2 500 € | À faire |
| Infrastructure (docker-compose #7, CI #8) | 3 000 € | 3 000 € | 0 € | Terminé |
| Pilotage et coordination transverse | 5 000 € | 1 500 € | 3 500 € | En cours |
| **Total Phase 1** | **25 000 €** | **18 000 €** | **7 000 €** | **72 % consommé** |

**Analyse** : aucun dépassement constaté. L'écart restant (7 000 €, 28 %)
correspond au reste à produire pour C6 et C7, cohérent avec l'avancement
réel du programme. Le poste « pilotage et coordination transverse »
absorbera la charge de rattrapage identifiée en CoSu (§1.2) sans nécessiter
de révision du budget prévisionnel de la Phase 1.

---

## 3. Encadrement du prestataire externe SupervIT

### 3.1 Périmètre de la mission

D'après la [feuille de route](feuille_de_route.md#2-composition-de-léquipe-projet),
SupervIT intervient en appui ponctuel encadré, principalement sur
l'intégration technique du bloc 4 (data lake OMEGA LAKE) — installation et
connexion des composants d'infrastructure (C19), où la complexité
technique dépasse le périmètre courant de l'équipe interne.

**Statut au 25/08/2026** : SupervIT n'est pas encore mobilisé. Le
programme est en Phase 1 (cadrage) ; la mobilisation est planifiée à
l'entrée en Phase 4, conformément au
[calendrier détaillé](feuille_de_route.md#41-diagramme-de-gantt).

### 3.2 Modalités d'encadrement prévues

| Élément | Détail |
|---|---|
| Point de contact interne | Data Engineer / chef·fe de projet (moi), avec appui de Sophie MARTIN (validation technique) |
| Cadence de suivi | Point bimensuel pendant la durée de la mission (Phase 4) |
| Livrables attendus | Rapport d'intervention à chaque point, documentation technique des composants installés, procédure d'installation reproductible (cohérent avec l'exigence transverse du cahier des charges, §9.4) |
| Critères de qualité | Revue systématique par la référente technique (Sophie MARTIN) avant acceptation d'un livrable |
| Critère d'éco-responsabilité | Intégré au cahier des charges de la mission dès sa contractualisation, conformément à la [stratégie RGESN](architecture_cible.md#5-stratégie-déco-responsabilité-rgesn) : préférence pour des solutions sobres et déjà retenues par le programme (MinIO plutôt qu'une solution propriétaire) |
| Périmètre budgétaire | Inclus dans le poste « Data lake et infrastructure IoT » de la Phase 4 (55 000 €, cf. feuille de route) — pas de ligne budgétaire séparée à ce stade |

### 3.3 Grille de suivi de mission (à activer en Phase 4)

| Intervention | Objet | Date prévue | Statut |
|---|---|---|---|
| Cadrage de la mission SupervIT | Définition du périmètre exact, contractualisation, critères de qualité et d'éco-responsabilité | Entrée en Phase 4 | Non démarré |
| Point d'intégration 1 | Installation du stockage objet et connexion du catalogue de données | Phase 4 | Non démarré |
| Point d'intégration 2 | Revue de la documentation d'installation et procédure de restauration | Phase 4 | Non démarré |

Cette grille sera complétée au fil de la Phase 4 ; elle est publiée dès
maintenant pour que les modalités d'encadrement soient actées avant la
mobilisation effective du prestataire.
