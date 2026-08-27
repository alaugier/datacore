# Séquencement du Bloc 3 — justification de l'ordre C13 à C17

Note courte, sur le même principe que
[`sequencement_bloc2.md`](sequencement_bloc2.md) mais volontairement plus
légère : contrairement au Bloc 2, l'ordre C13 → C14 → C15 ne fait pas
débat (dépendances évidentes déjà actées dans le Gantt de la
[feuille de route](feuille_de_route.md#41-diagramme-de-gantt), §4.1,
Phase 3). Seul le couple C16/C17 mérite d'être tranché explicitement.

---

## 1. C13 → C14 → C15 : confirmé sans réserve

| Étape | Dépend de | Raison |
|---|---|---|
| C13 — Modélisation étoile/flocon | Base de travail C11 peuplée | On ne peut pas concevoir des dimensions/faits sans connaître le contenu réel de la source (même logique qu'en Bloc 2 : modéliser après avoir touché la donnée) |
| C14 — Création de l'entrepôt | Schéma C13 arrêté | On ne crée pas physiquement des tables dont la structure n'est pas encore décidée |
| C15 — Pipelines ETL | Entrepôt C14 créé | Un pipeline alimente des tables cibles qui doivent déjà exister |

Aucune alternative sérieuse ici : modéliser avant de créer, créer avant
d'alimenter. Le Gantt (C13 7j → C14 7j → C15 10j, séquentiel) reflète
cette contrainte structurelle, pas seulement un choix de planning.

---

## 2. C16 vs C17 : l'ordre du Gantt est inversé

Le Gantt place **C16 (gestion opérationnelle) avant C17 (SCD2 sur
Dim_Client)**. Deux arguments, l'un de continuité technique, l'autre de
dépendance réelle côté RGPD, conduisent à retenir l'ordre inverse.

### 2.1 SCD2 est un prolongement direct de l'ETL (C15), pas de la gestion opérationnelle (C16)

La variation de dimension de type 2 (Kimball) sur `Dim_Client` est une
**technique d'implémentation ETL** : elle modifie la logique de
chargement (détection de changement, versionnement des lignes,
`valid_from`/`valid_to` ou `is_current`) sur un pipeline qui vient d'être
écrit en C15. Enchaîner C17 directement après C15 permet de rester dans
le même contexte technique (mêmes scripts, même logique de chargement en
tête), plutôt que d'interrompre ce travail par C16 (sauvegardes, SLA,
journalisation, RGPD — un tout autre registre de préoccupations) puis d'y
revenir.

### 2.2 Dépendance réelle identifiée : le registre RGPD de C16 ne peut pas être écrit correctement avant C17

L'issue #47 (C16) inclut explicitement *« registre RGPD et procédures de
tri des données personnelles de l'entrepôt »*, et l'issue #48 (C17)
porte sur `Dim_Client`, qui historisera des **changements d'adresse**
— donc une donnée personnelle, au même titre que `adresse_livraison` déjà
traitée dans le registre RGPD de la base de travail
([`registre_rgpd.md`](registre_rgpd.md)).

Si C16 est traité avant C17, la procédure de purge de `Dim_Client` doit
être conçue pour une table à une seule ligne par client — puis
entièrement revue dès que C17 la transforme en table à plusieurs lignes
historisées par client (une purge correcte doit alors couvrir *toutes*
les versions historiques d'un client, pas seulement la ligne courante).
C'est une dépendance réelle de C16 vers C17, pas seulement une question
d'ordonnancement pratique : concevoir le tri RGPD sur un schéma qui va
changer sous ses pieds produit un livrable à refaire.

### 2.3 Décision retenue

**C13 → C14 → C15 → C17 → C16**, contrairement à l'ordre du Gantt
(C13 → C14 → C15 → C16 → C17).

Ce choix n'invalide pas la feuille de route dans son principe (l'écart
porte sur l'ordre interne de deux tâches consécutives de 5 et 7 jours à
l'intérieur de la même phase, pas sur le calendrier global de la Phase
3) ; il corrige un enchaînement qui n'avait pas anticipé l'impact de C17
sur le périmètre RGPD de C16. À documenter dans le compte rendu de fin
de M2 comme écart justifié par rapport au Gantt initial.

---

## 3. Conséquence sur le suivi du milestone M2

Les 5 issues du milestone M2 restent celles déjà créées (#44 à #48) ;
seul l'ordre de traitement change (C17 avant C16). Le
[plan de développement](../plan_de_developpement.md) référence ce
document pour que l'ordre retenu reste traçable avant le démarrage du
codage, sur le même principe que pour le Bloc 2.
