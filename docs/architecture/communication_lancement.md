# Communication du programme et réunion de lancement — DATA CORE

**Compétence couverte : C7 — Communiquer tout au long de la réalisation du projet data**
**Épreuve associée : E3 (jeu de rôle « lancement d'un projet data »)**

Ce document rassemble les trois livrables attendus pour C7 : le plan de
communication du programme, les supports de la réunion de lancement
(conformes aux recommandations d'accessibilité) et la documentation
utilisateur des livrables du Bloc 1. Il s'appuie sur les parties prenantes
identifiées dans l'[étude de faisabilité](etude_faisabilite.md#33-parties-prenantes)
(C1) et sur le calendrier de la [feuille de route](feuille_de_route.md) (C5).

---

## 1. Plan de communication

| Partie prenante | Message clé | Canal | Fréquence | Responsable |
|---|---|---|---|---|
| Éléonore RAKOTO (sponsor) | Avancement stratégique, budget, risques, arbitrages nécessaires | Comité de suivi (CoSu) + synthèse écrite | Mensuelle | Chef·fe de projet |
| Karim BELAÏD (commanditaire opérationnel) | Avancement détaillé, arbitrages fonctionnels | Point d'équipe hebdomadaire + suivi Kanban (GitHub Projects) | Hebdomadaire | Chef·fe de projet |
| Équipe technique (Sophie MARTIN, Yanis DUPONT, Léa FONTAINE, Thomas NGUYEN) | Tâches, blocages, décisions techniques | Point d'équipe hebdomadaire + issues/PR GitHub | Hebdomadaire / continu | Chef·fe de projet |
| Responsables d'entrepôt (Lyon, Lille, Marseille) | Impacts opérationnels, formation aux nouveaux outils | Réunion de lancement + notes d'information | Ponctuelle (aux jalons majeurs) | Chef·fe de projet |
| Référents NordDrive, FreshMarket, MedioTex | Calendrier de disponibilité des nouveaux services (API, reporting) | Communication écrite | À chaque jalon majeur (fin de bloc) | Chef·fe de projet / Karim BELAÏD |
| SupervIT (prestataire) | Cahier des charges de mission, points d'intégration | Réunions bimensuelles (à partir de la Phase 4) | Bimensuelle en Phase 4 | Chef·fe de projet (cf. [supervision du programme](supervision_projet.md#3-encadrement-du-prestataire-externe-supervit)) |

**Principes transverses** : un seul canal de référence par type
d'information (le Kanban GitHub pour le suivi opérationnel, le CoSu pour
le pilotage stratégique) pour éviter la dispersion constatée sur les
anciens flux artisanaux ([étude de faisabilité §4.1](etude_faisabilite.md#41-problème-métier)) ;
accessibilité (RGAA) et sobriété (RGESN) appliquées à tous les supports de
communication, pas seulement aux livrables techniques.

---

## 2. Supports de la réunion de lancement

### 2.1 Déroulé de la réunion

| # | Séquence | Durée | Support |
|---|---|---|---|
| 1 | Accueil et objectifs de la réunion | 5 min | Introduction orale (§2.2) |
| 2 | Contexte et enjeux du programme | 10 min | Synthèse de l'[étude de faisabilité](etude_faisabilite.md) |
| 3 | Périmètre et architecture cible | 10 min | Synthèse de l'[architecture cible](architecture_cible.md) |
| 4 | Feuille de route, jalons, budget | 10 min | [Feuille de route](feuille_de_route.md) (Gantt, budget) |
| 5 | Rôles, responsabilités et rituels de suivi | 5 min | [Supervision du programme](supervision_projet.md) |
| 6 | Plan de communication | 5 min | §1 ci-dessus |
| 7 | Questions et échanges | 15 min | — |

**Consignes d'accessibilité appliquées à l'ensemble des supports** (RGAA) :
structure de titres hiérarchisée (un seul niveau H1 par support, sous-titres
en cascade) ; aucune information codée uniquement par la couleur (les
statuts Kanban sont toujours accompagnés d'un intitulé texte, jamais d'une
pastille de couleur seule) ; contraste suffisant sur les supports
projetés ; toute figure ou schéma projeté (ex. le schéma d'architecture en
couches) est accompagné d'une description orale et d'une alternative
textuelle dans le document support ; vocabulaire du glossaire métier
(voir [topographie des données §1](topographie_donnees.md#1-glossaire-métier))
rappelé en cas de jargon technique.

### 2.2 Introduction de la réunion (support d'animation, épreuve E3)

> Bonjour à toutes et à tous, et merci d'avoir libéré ce créneau.
>
> Je m'appelle [Data Engineer / chef·fe de projet] et je pilote, pour le
> compte de la Direction des Opérations, le programme DATA CORE — la
> refonte de l'infrastructure de données d'Omega Logistics.
>
> Nous sommes réunis aujourd'hui pour lancer officiellement ce programme.
> L'objectif de cette réunion est simple : nous assurer que chacune et
> chacun d'entre vous reparte avec la même compréhension du pourquoi de ce
> programme, de son périmètre, de son calendrier, et surtout de son rôle
> dans la réussite de ce projet.
>
> Pour rappel, ce programme part d'un constat partagé par Karim et par
> Éléonore : nos données — celles de FluxPro, de TransFlow, celles de nos
> clients NordDrive, FreshMarket et MedioTex — sont aujourd'hui dispersées,
> collectées site par site sans standardisation, et cela nous empêche
> d'avoir une vision fiable et consolidée de notre performance logistique.
> Nous allons, au travers de ce programme, centraliser cette collecte,
> construire un entrepôt de données pour piloter notre activité, puis nous
> préparer à l'arrivée des données massives de nos capteurs IoT.
>
> Ce lancement s'appuie sur quatre documents que je vous ai transmis en
> amont — l'étude de faisabilité, la topographie des données, l'étude
> d'architecture cible et la feuille de route — et je vous propose de les
> parcourir ensemble dans les prochaines minutes, avant de laisser toute la
> place à vos questions.
>
> Une dernière chose avant de commencer : ce programme se conduit dans le
> respect strict du RGPD, avec une attention particulière à
> l'accessibilité et à la sobriété de nos choix techniques. Ce ne sont pas
> des contraintes annexes : ce sont des conditions de réussite du
> programme, au même titre que le respect du calendrier et du budget.
>
> Je vous propose de commencer par un rappel du contexte.

---

## 3. Documentation utilisateur des livrables du Bloc 1

Index à destination des différentes parties prenantes, pour savoir quel
document consulter selon leur besoin.

| Livrable | Pour qui | Contenu | Où le trouver |
|---|---|---|---|
| Étude de faisabilité (C1) | Karim BELAÏD, Éléonore RAKOTO | Contexte, périmètre, opportunité, faisabilité, priorisation RICE, objectifs SMART | [`etude_faisabilite.md`](etude_faisabilite.md) |
| Topographie des données (C2) | Équipe technique | Glossaire métier, modèles de données des systèmes existants, flux, accès | [`topographie_donnees.md`](topographie_donnees.md) |
| Architecture cible (C3) | Équipe technique, DevOps | AS IS/TO BE, matrice des flux, RGPD, RGESN, RGAA | [`architecture_cible.md`](architecture_cible.md) |
| Veille technique et réglementaire (C4) | Équipe technique, Karim BELAÏD | Journal de veille hebdomadaire, décisions influencées | [`veille_technique_reglementaire.md`](veille_technique_reglementaire.md) |
| Feuille de route (C5) | Toutes les parties prenantes | Phases, équipe, budget, calendrier, outil de suivi | [`feuille_de_route.md`](feuille_de_route.md) |
| Supervision du programme (C6) | Karim BELAÏD, Éléonore RAKOTO | Rituels, suivi budgétaire, encadrement SupervIT | [`supervision_projet.md`](supervision_projet.md) |
| Communication et lancement (C7) | Toutes les parties prenantes | Ce document | [`communication_lancement.md`](communication_lancement.md) |
| Environnement technique (infra) | Équipe technique | Docker Compose (base de staging + API mock), pipeline CI | `infra/docker/`, `.github/workflows/ci.yml`, `README.md` |

**Comment utiliser cet index** : commencer par la feuille de route pour
une vue d'ensemble, puis approfondir selon son rôle — les responsables
d'entrepôt et les référents clients externes n'ont pas besoin des
documents techniques (C2, C3, infra), qui restent réservés à l'équipe
data ; Éléonore RAKOTO et Karim BELAÏD s'appuient prioritairement sur
l'étude de faisabilité, la feuille de route et le suivi budgétaire.

---

## 4. Synthèse pour l'épreuve E3

Ce document, avec la [feuille de route](feuille_de_route.md) (C5) et le
[document de supervision](supervision_projet.md) (C6), constitue le socle
documentaire de la réunion de lancement du programme DATA CORE. Le §2.2
sert directement de support à l'animation de l'introduction de cette
réunion devant les parties prenantes fictives.
