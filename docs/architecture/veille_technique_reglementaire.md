# Veille technique et réglementaire — DATA CORE

**Compétence couverte : C4 — Réaliser une veille technique et réglementaire**
**Épreuve associée : E2 (mise en situation professionnelle)**

Ce document est un journal vivant, mis à jour chaque semaine pendant toute
la durée du programme. Il couvre deux axes complémentaires à l'
[étude technique d'architecture](architecture_cible.md) (C3) : une veille
**technique** sur les pratiques d'orchestration de flux ETL (DataOps), et
une veille **réglementaire** sur les obligations RGPD et RGAA applicables
au programme. Chaque synthèse hebdomadaire est communiquée aux parties
prenantes (Karim BELAÏD, Éléonore RAKOTO, équipe technique) via le point
d'équipe hebdomadaire prévu dans la
[feuille de route](feuille_de_route.md#5-outil-de-suivi).

---

## 1. Méthodologie

| Élément | Détail |
|---|---|
| Fréquence | Hebdomadaire, synthèse rédigée chaque fin de semaine |
| Axes couverts | (1) Pratiques d'orchestration de flux ETL / DataOps ; (2) obligations RGPD et RGAA applicables au programme |
| Sources technique | Documentation officielle des outils (Apache Airflow, Dagster, Prefect, dbt, Great Expectations), retours d'expérience de la communauté DataOps |
| Sources réglementaire | CNIL (recommandations et guides pratiques), référentiel RGAA (DINUM), référentiel RGESN (DINUM/ADEME/Arcep) |
| Destinataires | Karim BELAÏD (commanditaire opérationnel), Éléonore RAKOTO (sponsor, synthèse mensuelle en CoSu), équipe technique (Sophie MARTIN, Yanis DUPONT, Léa FONTAINE, Thomas NGUYEN) |
| Format de diffusion | Synthèse courte (voir §2), point d'équipe hebdomadaire, archivage dans ce document |
| Critère de sélection | Un sujet n'est retenu que s'il a un impact direct sur une décision du programme (architecture, conformité, planning) — évite la veille "pour la forme" |

---

## 2. Journal de veille

### Semaine du 10/08/2026 (lancement du programme)

**Axe technique — orchestration de flux ETL légère.**
Comparatif rapide de trois orchestrateurs open source (Apache Airflow,
Dagster, Prefect) au regard du volume de données du programme (quelques
milliers de lignes par source en bloc 2, cf.
[topographie des données](topographie_donnees.md)). Airflow et Dagster
demandent une infrastructure dédiée (scheduler, base de métadonnées,
worker) disproportionnée pour ce volume ; Prefect propose un mode local
plus léger mais reste un outil supplémentaire à maintenir.
**Décision influencée** : conserver des scripts Python planifiés (cron)
pour le bloc 2, comme déjà acté dans l'
[étude technique d'architecture §2.3](architecture_cible.md#23-choix-technologiques-proposés),
et documenter l'évolution vers un orchestrateur dédié comme risque ouvert
si le volume augmente significativement (bloc 3-4).

**Axe réglementaire — géolocalisation de la flotte.**
Revue des recommandations de la CNIL sur la géolocalisation des véhicules
professionnels : information préalable des salariés, finalité limitée au
suivi logistique (exclusion du contrôle permanent d'activité), durée de
conservation courte des données de localisation précise, droit
d'opposition en dehors des horaires de travail.
**Décision influencée** : confirme le niveau de risque « zéro tolérance »
identifié par la sponsor dès l'
[étude de faisabilité](etude_faisabilite.md#5-étude-de-faisabilité) et la
durée de conservation courte proposée dans le
[registre RGPD de l'architecture cible](architecture_cible.md#42-registre-des-traitements-par-brique)
(purge de la géolocalisation brute au-delà de l'horizon défini).

### Semaine du 17/08/2026

**Axe technique — contrôle qualité des données dans les pipelines ETL.**
Tour d'horizon des pratiques DataOps de test de qualité de données
(assertions sur les schémas, unicité, valeurs manquantes) via des outils
comme Great Expectations ou les tests intégrés à dbt. Ces pratiques
formalisent un principe déjà identifié empiriquement lors de la
[topographie des données](topographie_donnees.md#33-fichiers-clients-bruts--formats-hétérogènes)
(taux de doublons mesurés entre 55 et 68 % sur les fichiers clients).
**Décision influencée** : les contrôles qualité (unicité, doublons,
formats) prévus pour l'agrégation des fichiers clients (bloc 2, C10) et
pour les pipelines ETL de l'entrepôt (bloc 3, C15) seront formalisés sous
forme d'assertions explicites et testées, plutôt que de simples scripts
de nettoyage ad hoc.

**Axe réglementaire — accessibilité numérique (RGAA).**
Lecture des critères du référentiel RGAA (version 4.1, DINUM) applicables
à une documentation technique et à un futur tableau de bord : structure
sémantique des titres, alternatives textuelles, contraste des couleurs,
navigation au clavier.
**Décision influencée** : confirme les engagements pris dans la
[stratégie d'accessibilité de l'architecture cible](architecture_cible.md#6-stratégie-daccessibilité-numérique-rgaa),
en particulier la nécessité de tester la compatibilité avec un lecteur
d'écran, remontée concrètement par les responsables d'entrepôt lors des
entretiens de cadrage (site de Lille).

### Semaine du 24/08/2026

**Axe technique — stockage objet compatible S3 pour le futur data lake.**
Comparatif de solutions de stockage objet auto-hébergeables (MinIO) face
à des offres cloud propriétaires (dont Microsoft Fabric / OneLake),
au regard de la contrainte de fonctionnement local du programme.
**Décision influencée** : confirme et documente le choix de MinIO déjà
acté dans l'
[étude technique d'architecture §2.5](architecture_cible.md#25-alternative-écartée--microsoft-fabric)
(contrainte pédagogique de fonctionnement local, coût, reproductibilité).

**Axe réglementaire — éco-conception des services numériques (RGESN).**
Lecture des critères du référentiel général d'éco-conception des services
numériques (RGESN, DINUM/ADEME/Arcep) applicables aux choix d'hébergement,
de sobriété des requêtes et de cycle de vie des données.
**Décision influencée** : confirme les principes déjà retenus dans la
[stratégie d'éco-responsabilité de l'architecture cible](architecture_cible.md#5-stratégie-déco-responsabilité-rgesn)
(pagination systématique des API, absence de duplication inutile des
données entre les briques).

---

## 3. Synthèse consolidée

| Semaine | Axe technique | Axe réglementaire | Impact concret |
|---|---|---|---|
| 10/08/2026 | Orchestrateurs ETL légers (Airflow/Dagster/Prefect vs cron) | Géolocalisation de flotte (CNIL) | Confirme le choix cron pour le bloc 2 ; confirme la purge courte de la géolocalisation |
| 17/08/2026 | Contrôle qualité des données (Great Expectations, tests dbt) | Accessibilité numérique (RGAA 4.1) | Formalisation des contrôles qualité C10/C15 ; engagement lecteur d'écran confirmé |
| 24/08/2026 | Stockage objet S3 (MinIO vs cloud propriétaire) | Éco-conception (RGESN) | Confirme le choix MinIO ; confirme sobriété des requêtes/données |

Cette veille est un processus continu : les prochaines synthèses
hebdomadaires seront ajoutées à ce journal au fil du programme, notamment
lors de l'entrée dans le bloc 2 (choix d'outils d'extraction et de
scraping) et à l'approche du bloc 4 (catalogues de données, gouvernance
des accès).
