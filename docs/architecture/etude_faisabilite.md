# Étude de faisabilité du programme DATA CORE

**Compétence couverte : C1 — Analyser l'expression d'un besoin de projet data**
**Épreuves associées : E1 (étude de cas), E2 (mise en situation professionnelle)**

Auteur : Data Engineer / chef·fe de projet DATA CORE
Commanditaire : Éléonore RAKOTO, Directrice des Opérations — Omega Logistics
Commanditaire opérationnel : Karim BELAÏD, Responsable du Pôle Data

---

## 1. Contexte

Omega Logistics est un prestataire logistique (3PL) opérant sur trois sites
(Lyon, Lille, Marseille) pour le compte de trois clients aux besoins très
différents : NordDrive (pièces automobiles, flux tendus), FreshMarket
(grande distribution alimentaire, contraintes de température et de
traçabilité) et MedioTex (textile, forte saisonnalité).

L'exploitation s'appuie sur deux systèmes historiques :

- **FluxPro** (WMS) — pilotage des entrepôts : commandes, stocks,
  expéditions, lignes de commande ;
- **TransFlow** (TMS) — organisation des tournées de la flotte de
  transport.

Les flux de collecte et de transformation de données ont été développés
site par site, de façon artisanale, sans standardisation ni documentation
commune. Cette dispersion génère des erreurs, des incidents récurrents et
empêche la Direction des Opérations d'obtenir une vision consolidée et
fiable de l'activité (taux de service, délais, coûts, stocks).

C'est dans ce contexte qu'Éléonore RAKOTO confie au Pôle Data, représenté
par Karim BELAÏD, le cadrage du programme **DATA CORE** : refonte de
l'infrastructure data d'Omega Logistics. La présente étude constitue la
première étape de ce cadrage (compétence C1, activité A1) et s'appuie sur
des entretiens menés auprès des principales parties prenantes.

---

## 2. Grilles d'entretien

Trois entretiens fictifs ont été construits pour recueillir l'expression du
besoin à différents niveaux de l'organisation : stratégique (sponsor),
opérationnel data (commanditaire direct) et terrain (utilisateurs finaux).

### 2.1 Entretien avec Karim BELAÏD — Responsable du Pôle Data

*Rôle : commanditaire opérationnel du programme. Objectif de l'entretien :
cerner le périmètre technique, les irritants actuels et les contraintes de
mise en œuvre.*

| # | Question posée | Réponse recueillie |
|---|---|---|
| 1 | Quels sont aujourd'hui les principaux irritants sur la donnée chez Omega Logistics ? | « Chaque site a bricolé ses propres extractions FluxPro dans des scripts Excel ou des requêtes SQL ad hoc, sans revue ni tests. Un incident sur un site n'est jamais visible depuis les autres. On découvre les erreurs de stock a posteriori, souvent signalées par un client. » |
| 2 | Combien de sources de données faut-il couvrir, et sous quels formats ? | « FluxPro (7 tables relationnelles), TransFlow (API interne), le portail d'un transporteur externe à consulter manuellement aujourd'hui, les fichiers de commandes envoyés par nos 3 clients — chacun dans un format différent — et bientôt les capteurs IoT des entrepôts (température, RFID, géoloc flotte, comptage caméra). » |
| 3 | Quelles compétences et quels outils sont disponibles en interne ? | « Une Lead Data Engineer (Sophie MARTIN), un Data Engineer (Yanis DUPONT), une Data Analyst (Léa FONTAINE), et un DevOps (Thomas NGUYEN) en support infra/sécurité. On peut aussi mobiliser un prestataire externe, SupervIT, pour l'intégration technique, mais son périmètre doit être cadré et supervisé. » |
| 4 | Quelles contraintes techniques ou budgétaires dois-je anticiper ? | « Le budget indicatif du programme est de 180 000 €, réparti sur les 4 blocs. Aucun outil n'est imposé : choisissez ce qui est le plus robuste et le plus simple à maintenir par l'équipe. Attention à ne pas sur-dimensionner : on démarre avec un volume raisonnable (25 000 lignes d'historique), mais l'arrivée des capteurs IoT va faire changer d'échelle. » |
| 5 | Quel est le niveau de maturité data actuel de l'organisation ? | « Faible sur la gouvernance : pas de registre RGPD à jour, pas de catalogue de données, pas de documentation partagée. Correct sur la donnée transactionnelle brute : FluxPro est fiable à la source, le problème est en aval. » |
| 6 | Qu'attendez-vous concrètement de moi en premier livrable ? | « Une étude de faisabilité qui pose clairement le périmètre, les risques, et qui priorise ce qu'on doit traiter en premier — je ne veux pas d'un audit théorique de 40 pages, je veux des conclusions actionnables pour arbitrer avec la direction. » |

### 2.2 Entretien avec Éléonore RAKOTO — Directrice des Opérations

*Rôle : sponsor du programme, décisionnaire budgétaire. Objectif de
l'entretien : cerner les enjeux stratégiques, le retour attendu et le
niveau de risque acceptable.*

| # | Question posée | Réponse recueillie |
|---|---|---|
| 1 | Pourquoi lancer ce programme maintenant ? | « Parce qu'on ne peut plus piloter l'activité sans données fiables. Nos clients — NordDrive en particulier — nous demandent des indicateurs de taux de service que je ne peux pas leur fournir de façon consolidée aujourd'hui. Je découvre les problèmes de stock ou de retard après coup, jamais en amont. » |
| 2 | Quels indicateurs business sont prioritaires pour vous ? | « Taux de service par client et par site, délais de livraison, niveaux de stock, coûts de transport. Si dans 6 mois je peux ouvrir un tableau de bord et répondre en direct à un client sur sa performance logistique, le programme aura rempli son rôle. » |
| 3 | Quel est le niveau de risque que vous êtes prête à accepter ? | « Faible sur la continuité d'exploitation — FluxPro et TransFlow ne doivent jamais être perturbés par le programme. Modéré sur le calendrier : je préfère un jalon décalé à un livrable bâclé. Zéro tolérance sur la conformité RGPD, surtout avec les données de géolocalisation des chauffeurs. » |
| 4 | Quelles contraintes réglementaires ou d'image dois-je prendre en compte ? | « RGPD bien sûr, mais aussi l'accessibilité de nos outils — on a des collaborateurs en situation de handicap sur les sites, et l'éco-responsabilité fait partie de notre politique RSE : on communique dessus auprès de nos clients grande distribution. » |
| 5 | Quel est le retour sur investissement attendu ? | « Moins d'incidents opérationnels liés aux erreurs de données, moins de temps passé par les équipes à réconcilier des fichiers à la main, et une meilleure rétention client grâce à un reporting fiable et rapide. » |
| 6 | Quel est votre niveau d'implication souhaité pendant le programme ? | « Je veux un point mensuel en comité de suivi (CoSu), et être alertée immédiatement en cas de risque sur le calendrier ou le budget. Le reste, je fais confiance au Pôle Data. » |

### 2.3 Entretien avec les responsables d'entrepôt (Lyon, Lille, Marseille)

*Rôle : utilisateurs finaux et exploitants terrain. Entretien mené en
groupe (les trois responsables partagent des irritants très proches).
Objectif : recueillir les besoins opérationnels quotidiens et les
contraintes d'usage terrain.*

| # | Question posée | Réponse recueillie |
|---|---|---|
| 1 | Comment utilisez-vous les données de FluxPro au quotidien ? | « On consulte les stocks et les commandes du jour directement dans FluxPro, mais dès qu'on a besoin d'un historique ou d'une vue multi-site, on demande une extraction au Pôle Data, avec plusieurs jours de délai. » |
| 2 | Quels sont vos irritants les plus fréquents ? | « Lyon : les ruptures de stock ne sont détectées que lorsqu'une commande échoue, pas en amont. Lille : on n'a aucune visibilité sur les tournées TransFlow en cours, on appelle les chauffeurs pour savoir où ils en sont. Marseille : les fichiers clients FreshMarket arrivent dans un format qui ne correspond jamais exactement à celui attendu, ça génère des ressaisies manuelles. » |
| 3 | Quel outillage utilisez-vous aujourd'hui pour compenser ces manques ? | « Des fichiers Excel partagés, mis à jour à la main, différents d'un site à l'autre — ce qui fait qu'on ne peut jamais comparer directement nos indicateurs. » |
| 4 | Quels capteurs ou équipements sont déjà en place ou prévus sur vos sites ? | « Des sondes de température sur les zones froides (obligatoire pour FreshMarket), des lecteurs RFID en cours de déploiement sur les palettes, et des caméras de comptage aux quais de chargement. La géolocalisation de la flotte est gérée par TransFlow. » |
| 5 | Qu'attendez-vous d'un futur outil de pilotage ? | « Une vue simple, par site, mise à jour au moins une fois par jour, avec des alertes automatiques sur les ruptures de stock et les retards de livraison. Pas besoin d'un outil compliqué : on veut de la fiabilité et de la rapidité. » |
| 6 | Avez-vous des contraintes d'accessibilité ou d'ergonomie à signaler ? | « Sur le site de Lille, un des membres de l'équipe logistique utilise un lecteur d'écran : les futurs outils et documents doivent rester compatibles avec ces usages. » |

---

## 3. Périmètre fonctionnel

### 3.1 Dans le périmètre du programme DATA CORE

- Centralisation et fiabilisation de la collecte des données FluxPro (WMS),
  TransFlow (TMS) et des flux clients (NordDrive, FreshMarket, MedioTex).
- Nettoyage, agrégation et mise à disposition industrialisée des données
  (base de données de travail, API REST documentée).
- Construction d'un entrepôt de données décisionnel (OMEGA BI) pour le
  pilotage de la performance logistique par client, site et période.
- Conception d'un data lake (OMEGA LAKE) pour absorber la montée en charge
  liée aux données massives et hétérogènes : capteurs IoT (température,
  RFID), géolocalisation de la flotte, vidéo de comptage.
- Mise en conformité RGPD, prise en compte de l'éco-responsabilité (RGESN)
  et de l'accessibilité (RGAA) sur l'ensemble des livrables.

### 3.2 Hors périmètre

- Remplacement ou refonte de FluxPro et TransFlow eux-mêmes : le programme
  s'appuie sur ces systèmes existants, il ne les remplace pas.
- Développement d'interfaces métier avancées (front-end de pilotage riche)
  au-delà des tableaux de bord et de l'API de mise à disposition des
  données.
- Intégration de nouvelles sources de données réelles autres que celles
  fournies dans le pack technique `datacore-dataset` (aucune donnée réelle
  ni accès externe n'est requis pour la formation).
- Déploiement en production sur une infrastructure cloud réelle : le
  programme est mené dans un cadre pédagogique, sur environnement local ou
  de démonstration.

### 3.3 Parties prenantes

| Partie prenante | Rôle | Niveau d'implication |
|---|---|---|
| Éléonore RAKOTO | Sponsor du programme | Décisionnaire |
| Karim BELAÏD | Commanditaire opérationnel | Décisionnaire, contributeur |
| Data Engineer / chef·fe de projet (moi) | Pilotage et réalisation | Contributeur principal |
| Sophie MARTIN (Lead Data Engineer) | Référente technique | Contributeur, valideur technique |
| Yanis DUPONT (Data Engineer) | Équipe technique | Contributeur |
| Léa FONTAINE (Data Analyst) | Équipe technique / utilisatrice | Contributeur, utilisateur |
| Thomas NGUYEN (DevOps) | Support infrastructure et sécurité | Contributeur |
| Responsables d'entrepôt (Lyon, Lille, Marseille) | Utilisateurs finaux | Utilisateur, contributeur ponctuel |
| Référents NordDrive, FreshMarket, MedioTex | Clients externes | Consulté, destinataire des livrables |
| SupervIT | Prestataire d'intégration technique | Contributeur externe, encadré |

---

## 4. Étude d'opportunité

### 4.1 Problème métier

L'absence de centralisation et de standardisation des flux de données
génère trois catégories d'impact :

1. **Opérationnel** : détection tardive des incidents (ruptures de stock,
   retards de livraison), ressaisies manuelles liées aux formats
   hétérogènes des fichiers clients, absence de visibilité en temps réel
   sur les tournées.
2. **Décisionnel** : impossibilité pour la Direction des Opérations
   d'obtenir une vision consolidée et fiable de la performance logistique
   par client, site et période.
3. **Conformité et risque** : absence de registre RGPD à jour, absence de
   catalogue de données, exposition non maîtrisée de données sensibles
   (géolocalisation des chauffeurs, contacts clients).

### 4.2 Enjeux pour Omega Logistics

- **Satisfaction et rétention client** : NordDrive, FreshMarket et
  MedioTex attendent un reporting fiable de leur taux de service ; son
  absence est un risque commercial direct.
- **Maîtrise des coûts** : le temps actuellement passé par les équipes à
  réconcilier manuellement des données représente un coût caché
  récurrent.
- **Anticipation de la croissance** : le déploiement progressif de
  capteurs IoT sur les trois sites va multiplier le volume et la variété
  des données sans solution de stockage adaptée si rien n'est fait.
- **Conformité réglementaire** : le RGPD impose un traitement documenté et
  maîtrisé des données personnelles (chauffeurs, clients), avec un niveau
  de risque jugé « zéro tolérance » par la sponsor du programme.

### 4.3 Bénéfices attendus

| Bénéfice | Bénéficiaire principal |
|---|---|
| Réduction du délai de détection des incidents (rupture de stock, retard) | Responsables d'entrepôt |
| Vision consolidée et fiable de la performance logistique | Direction des Opérations |
| Réduction du temps de traitement manuel des fichiers clients | Pôle Data |
| Mise à disposition industrialisée des données via une API documentée | Équipes BI et data science |
| Conformité RGPD, RGAA et RGESN démontrable | Direction des Opérations, clients |
| Capacité à absorber la montée en charge des données IoT | Pôle Data, DevOps |

### 4.4 Solutions alternatives envisagées

| Option | Description | Avis |
|---|---|---|
| Ne rien faire | Conserver les flux artisanaux actuels | Rejetée : risque opérationnel et commercial croissant, non conforme RGPD |
| Achat d'une solution BI/ETL propriétaire clé en main | Souscription à un outil SaaS intégré | Écartée à ce stade : coût élevé, dépendance fournisseur, ne couvre pas le besoin de data lake ni la maîtrise technique interne visée par le Pôle Data |
| Programme interne DATA CORE (retenu) | Construction progressive, par le Pôle Data, d'une chaîne de collecte, d'un entrepôt de données et d'un data lake, avec un prestataire externe encadré sur l'intégration | Retenue : maîtrise interne des compétences, coût maîtrisé (180 000 €), adaptée à la taille et à la trajectoire d'Omega Logistics |

---

## 5. Étude de faisabilité

### 5.1 Faisabilité technique

- **Sources de données** : les cinq types de sources attendus par le
  référentiel (service web, page à scraper, fichier de données, base de
  données, système big data) sont couverts par le pack technique
  `datacore-dataset` fourni : API TransFlow, portail transporteur,
  fichiers clients, export FluxPro (`data/*.csv` + `data/schema.sql`),
  historique volumineux (25 000 lignes).
- **Compétences internes** : l'équipe (Lead Data Engineer, Data Engineer,
  Data Analyst, DevOps) couvre les compétences nécessaires à la collecte,
  au stockage et à l'exposition des données ; SupervIT vient en appui sur
  l'intégration technique.
- **Aucun outil imposé** : le programme peut s'appuyer sur des solutions
  open source ou déjà maîtrisées par l'équipe, ce qui réduit le risque
  d'adoption et de coût de licence.
- **Point de vigilance** : la montée en charge liée à l'IoT (bloc 4)
  nécessitera un choix d'architecture data lake capable d'absorber un flux
  temps réel (`/api/stream/capteurs`) en plus du batch — à traiter dans
  l'étude technique d'architecture (C3).

### 5.2 Faisabilité organisationnelle

- Gouvernance déjà identifiée : sponsor (Éléonore RAKOTO), commanditaire
  opérationnel (Karim BELAÏD), comité de suivi mensuel (CoSu) souhaité par
  la sponsor.
- Équipe projet existante et disponible, avec des rôles clairs
  (référente technique, contributeurs, support infra).
- Le prestataire externe SupervIT devra être cadré contractuellement et
  suivi dans le cadre du programme (compétence C6).
- Risque organisationnel identifié : la dispersion historique des
  pratiques site par site peut générer des résistances au changement chez
  les responsables d'entrepôt ; à anticiper par la communication (C7) et
  l'implication des utilisateurs finaux dès le cadrage.

### 5.3 Faisabilité financière

- Budget indicatif de 180 000 € réparti sur les 4 blocs (25 000 € pour le
  cadrage, 45 000 € pour la collecte/stockage/API, 55 000 € pour
  l'entrepôt de données, 55 000 € pour le data lake).
- L'absence de contrainte d'outillage imposé permet de privilégier des
  solutions open source, réduisant le risque de dépassement budgétaire
  lié à des licences.
- Faisabilité jugée réaliste au regard du périmètre fonctionnel défini en
  section 3, sous réserve de respecter le séquencement en 4 phases (voir
  feuille de route, compétence C5).

### 5.4 Faisabilité juridique et réglementaire (RGPD)

- Données personnelles identifiées : coordonnées des chauffeurs
  (TransFlow, géolocalisation), contacts clients (fichiers clients,
  FluxPro).
- Niveau de risque « zéro tolérance » exprimé par la sponsor : nécessite
  un registre des traitements tenu à jour dès la base de staging, une
  politique de pseudonymisation et des procédures de purge, dès le bloc 2
  (C11) et renforcées au bloc 4 (C21) pour la géolocalisation.
- Faisabilité jugée conditionnée à l'intégration de ces exigences dès la
  conception (privacy by design), et non en correction a posteriori.

### 5.5 Faisabilité liée à l'accessibilité et à l'éco-responsabilité

- Un besoin d'accessibilité concret a été remonté en entretien (lecteur
  d'écran, site de Lille) : les documents et interfaces produits devront
  respecter le RGAA.
- L'éco-responsabilité fait partie de la politique RSE d'Omega Logistics
  et doit être prise en compte dans le choix des outils et du prestataire
  SupervIT (référentiel RGESN), sans remettre en cause la faisabilité
  technique du programme.

### 5.6 Synthèse de faisabilité

| Dimension | Verdict | Niveau de risque résiduel |
|---|---|---|
| Technique | Faisable — pack technique complet, compétences internes couvrant les besoins | Faible |
| Organisationnelle | Faisable — gouvernance et équipe en place | Moyen (conduite du changement terrain) |
| Financière | Faisable — budget cohérent avec le périmètre défini | Faible |
| Juridique / RGPD | Faisable sous condition de privacy by design | Moyen (géolocalisation chauffeurs) |
| Accessibilité / éco-responsabilité | Faisable — exigences claires et intégrables dès le cadrage | Faible |

**Conclusion** : le programme DATA CORE est jugé faisable dans le
périmètre, le budget et le calendrier envisagés, sous réserve de traiter
en priorité la conformité RGPD dès la conception et d'accompagner le
changement auprès des responsables d'entrepôt.

---

## 6. Analyse RICE

L'analyse RICE (Reach, Impact, Confidence, Effort) priorise les grands
chantiers identifiés lors des entretiens, afin d'éclairer la feuille de
route du programme (compétence C5). Échelles utilisées : Reach (nombre
d'utilisateurs/sites impactés, sur 10), Impact (1 = mineur à 3 = massif),
Confidence (probabilité de succès, en %), Effort (personne-mois estimés).

Score RICE = (Reach × Impact × Confidence) / Effort

| Chantier | Reach | Impact | Confidence | Effort (p.m.) | Score RICE | Priorité |
|---|---|---|---|---|---|---|
| Centraliser la collecte FluxPro + fichiers clients | 10 | 3 | 0,9 | 2 | 13,5 | 1 |
| API REST de mise à disposition des données consolidées | 8 | 2 | 0,9 | 2 | 7,2 | 2 |
| Entrepôt de données OMEGA BI (taux de service, délais, stocks) | 9 | 3 | 0,7 | 4 | 4,7 | 3 |
| Registre RGPD et pseudonymisation des données sensibles | 10 | 3 | 0,9 | 3 | 9,0 | 2 (transverse, non séquençable) |
| Automatisation de la collecte portail transporteur (scraping) | 6 | 1 | 0,8 | 1 | 4,8 | 4 |
| Data lake OMEGA LAKE (IoT batch + streaming) | 6 | 2 | 0,5 | 5 | 1,2 | 5 |
| Catalogue de données et gouvernance par groupes d'accès | 5 | 2 | 0,6 | 3 | 2,0 | 5 |

**Lecture** : la centralisation de la collecte FluxPro/clients et la mise
en conformité RGPD ressortent comme prioritaires — elles conditionnent la
fiabilité de tous les livrables suivants. L'entrepôt de données OMEGA BI
arrive ensuite, car il répond directement à la demande prioritaire de la
sponsor (indicateurs consolidés). Le data lake, plus complexe et incertain
(confidence 0,5 du fait de la nouveauté du flux temps réel), est
volontairement positionné en dernière phase, ce qui est cohérent avec le
découpage du programme en 4 blocs séquentiels.

---

## 7. Objectifs SMART

| # | Objectif | Spécifique | Mesurable | Acceptable / Ambitieux | Réaliste | Temporellement défini |
|---|---|---|---|---|---|---|
| 1 | Centraliser 100 % des données FluxPro, TransFlow et fichiers clients dans une base de travail unique, documentée | Import des 7 tables FluxPro, extraction API TransFlow, agrégation des 3 flux clients | 100 % des sources listées en section 3 intégrées, script d'import versionné | Validé par Karim BELAÏD comme priorité n°1 | S'appuie sur le pack technique déjà fourni | Fin de la phase 2 (bloc 2) du programme |
| 2 | Exposer une API REST documentée permettant aux équipes BI d'accéder au jeu de données consolidé | API sécurisée, spécification OpenAPI | Disponibilité de l'API testée, documentation publiée | Cohérent avec les compétences internes de l'équipe technique | Techniquement standard (authentification + endpoints CRUD) | Fin de la phase 2 (bloc 2) du programme |
| 3 | Mettre à disposition un tableau de bord du taux de service, des délais et des coûts par client, site et période | Indicateurs définis avec Éléonore RAKOTO en entretien | Tableau de bord consultable, alimenté depuis OMEGA BI | Répond directement à l'attente exprimée par la sponsor | Basé sur l'entrepôt de données construit au bloc 3 | Fin de la phase 3 (bloc 3) du programme |
| 4 | Réduire à zéro les traitements de données personnelles non répertoriés dans un registre RGPD | Registre des traitements tenu à jour pour chaque brique (staging, entrepôt, data lake) | Registre existant, revu à chaque jalon, 0 traitement non documenté à la clôture | Aligné sur le niveau de risque « zéro tolérance » exprimé par la sponsor | Processus de documentation intégré dès la conception | Continu, avec revue à chaque fin de phase |
| 5 | Concevoir une architecture de data lake capable d'ingérer le flux temps réel de capteurs et les données IoT batch existantes | Zones raw / staging / curated, connecteur batch et streaming opérationnels | Ingestion testée sur les fichiers `data/iot/*` et le flux `/api/stream/capteurs` | Ambitieux mais nécessaire face à la montée en charge annoncée | Le pack technique fournit déjà les données et le flux à ingérer | Fin de la phase 4 (bloc 4) du programme |

---

## 8. Conclusion et recommandation

L'étude confirme la faisabilité du programme DATA CORE dans le périmètre,
le calendrier en 4 phases et le budget de 180 000 € envisagés. Les
entretiens menés auprès de Karim BELAÏD, d'Éléonore RAKOTO et des
responsables d'entrepôt convergent sur un même constat : la donnée
existe et est globalement fiable à la source (FluxPro), mais son absence
de centralisation, de standardisation et de gouvernance empêche
aujourd'hui son exploitation décisionnelle et expose l'organisation à un
risque de conformité RGPD.

**Recommandation** : lancer le programme selon le séquencement proposé par
l'analyse RICE — collecte et fiabilisation des données en priorité
(bloc 2, avec le registre RGPD dès cette étape), puis entrepôt décisionnel
OMEGA BI (bloc 3), puis data lake OMEGA LAKE (bloc 4) — en conservant le
cadrage (bloc 1, présente étude incluse) comme fondation commune aux trois
blocs suivants.

Cette étude de faisabilité alimente directement les livrables suivants du
bloc 1 : topographie des données (C2), étude technique d'architecture
AS IS / TO BE (C3) et feuille de route du programme (C5).
