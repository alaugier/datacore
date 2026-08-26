# Séquencement du Bloc 2 — justification de l'ordre C8 à C12

Note de décision, sur le même principe que l'
[analyse RICE de l'étude de faisabilité](etude_faisabilite.md#6-analyse-rice) :
documenter explicitement un choix d'ordonnancement avant de coder, plutôt
que de laisser un flou implicite — le type de flou qui avait conduit au
gap C4/C6/C7 détecté après coup en fin de M0 (voir
[compte rendu M0](../comptes_rendus/M0.md)). Ici, le même type de gap est
anticipé et traité **avant** le développement, pas après.

---

## 1. Question posée

Le cahier des charges (§6, « Étapes suggérées ») propose implicitement
l'ordre C8/C9/C10 (extraction et nettoyage) puis C11 (modélisation MERISE
et création de la base de travail) puis C12 (API). Une autre approche,
plus classique en conception de base de données, consisterait à modéliser
la base cible (C11) **avant** d'écrire les scripts d'extraction, en
s'appuyant sur la [topographie des données](topographie_donnees.md) (C2)
déjà produite — qui documente déjà en détail les schémas de toutes les
sources. L'infrastructure de staging existe même déjà partiellement
(`infra/docker/docker-compose.yml`, `scripts/init_staging_db.sh`, issue
#7), ce qui pourrait laisser penser que C11 est en partie déjà entamée.

**Ce document tranche cette question et explique pourquoi.**

## 2. Ce que fait déjà l'infrastructure existante (issue #7) — et ce qu'elle ne fait pas

`scripts/init_staging_db.sh` importe le schéma **FluxPro tel que fourni**
(`data/raw/schema.sql`, 7 tables) dans la base de staging PostgreSQL. C'est
un **bootstrap technique** (démarrer une base disponible pour développer),
pas le livrable C11 : le schéma FluxPro n'est pas un schéma que nous avons
conçu, et il ne couvre qu'une seule des cinq sources du programme. Le
livrable C11 attendu est un **schéma MERISE que nous concevons**, pour la
base de travail **consolidée** qui doit accueillir FluxPro **et**
TransFlow **et** les fichiers clients nettoyés **et** l'historique — un
travail de modélisation distinct, à ne pas confondre avec l'import déjà
réalisé.

## 3. Analyse des dépendances entre compétences

| Compétence | Entrée nécessaire | Sortie produite |
|---|---|---|
| C8 — Extraction multi-source | Sources brutes (API TransFlow, portail, fichiers clients, historique) | Données brutes extraites, scripts versionnés |
| C10 — Agrégation/nettoyage clients | Fichiers clients bruts extraits par C8 | Jeu de données clients unique et propre |
| C9 — Requêtes SQL documentées | Base FluxPro déjà importée (#7) + historique chargé | Requêtes documentées, connaissance fine des données réelles |
| C11 — Modélisation MERISE + base de travail | Données réellement extraites et nettoyées (C8/C9/C10), + schémas connus depuis C2 | Base de travail consolidée, registre RGPD |
| C12 — API Omega Data | Base de travail peuplée (C11) | API REST documentée |

**Lecture** : C11 a deux dépendances possibles — soit uniquement la
connaissance *abstraite* des schémas (déjà acquise via C2), soit la
connaissance *concrète* des données réellement extraites et nettoyées
(C8/C9/C10). C12 dépend structurellement de C11 dans tous les cas : il ne
peut exposer une base qui n'existe pas encore.

## 4. Comparaison des deux ordres possibles

| | Option A — Extraction d'abord (C8→C10→C9→C11→C12) | Option B — Modélisation d'abord (C11→C8→C10→C9→C12) |
|---|---|---|
| Principe | Extraire et nettoyer concrètement, puis modéliser la base à partir des données réellement observées | Concevoir le schéma cible à partir de la topographie déjà documentée (C2), puis extraire pour le peupler |
| Risque principal | Aucun schéma cible pendant l'extraction : risque de scripts C8 qui écrivent vers des structures provisoires, à adapter ensuite | Schéma conçu sur la base d'une connaissance *abstraite* (C2) ; risque de devoir le corriger si les données réelles révèlent des cas non anticipés par la topographie (ex. valeurs de `statut` non recensées, doublons inter-sources) |
| Cohérence avec le cahier des charges | Ordre suggéré explicitement (§6, étapes 1 à 7) | Contredit l'ordre suggéré, sans bénéfice de conformité supplémentaire (le référentiel n'impose pas d'ordre strict, mais la trame pédagogique du livret le sous-entend) |
| Cohérence avec le principe RGPD *by design* déjà acté en C3 | Le registre RGPD (livrable C11) arrive après le design architectural du RGPD (déjà fait en C3, `architecture_cible.md` §4) — pas de contradiction : C3 a posé le cadre, C11 en est la mise en œuvre opérationnelle une fois les données réelles en main | Anticipe légèrement plus tôt la mise en œuvre opérationnelle du registre, mais sans donnée réelle à enregistrer avant C8 — peu de bénéfice concret |
| Précédent dans le programme | Aligné avec la pratique déjà suivie en Bloc 1 : la topographie (C2) a *précédé* l'architecture cible (C3), qui a elle-même précédé la feuille de route (C5) — connaître le terrain avant de modéliser | — |

## 5. Décision retenue

**Option A : C8 → C10 → C9 → C11 → C12.**

Justification principale : la [topographie des données](topographie_donnees.md)
(C2) donne une connaissance fiable des *schémas* de chaque source, mais
pas de leur *contenu réel* une fois extrait et nettoyé — en particulier
les taux de doublons mesurés (13 à 17 % au grain commande/produit sur les
fichiers clients, cf. C2 §3.3) montrent que la réalité des données dépasse
ce qu'un schéma abstrait peut anticiper (valeurs de repli, cas de
rapprochement entre `tracking_number` FluxPro et TransFlow, etc.). Le
traitement concret de C10 a d'ailleurs révélé que le premier chiffre
publié en C2 (mesuré au grain « commande » seul) surestimait fortement le
phénomène, en confondant commandes multi-produits légitimes et vrais
doublons — la correction elle-même illustre l'argument : l'analyse
abstraite ne suffit pas, le contact direct avec la donnée réelle affine
la compréhension. Modéliser la base de travail (C11) *après* avoir
concrètement extrait et nettoyé les données limite le risque de devoir
revoir le schéma MERISE en cours de route. Cet ordre est de plus celui
suggéré par le cahier des charges, sans qu'aucun argument technique ne
justifie de s'en écarter ici.

Ordre détaillé retenu et justification pas à pas :

1. **C8 — Extraction multi-source** en premier : ne nécessite aucune
   décision de modélisation, uniquement de faire parler chaque source
   fidèlement. Point de départ à risque le plus faible.
2. **C10 — Agrégation/nettoyage des fichiers clients** : dépend
   directement des fichiers bruts lus par C8 ; produit le premier jeu de
   données propre et unique.
3. **C9 — Requêtes SQL documentées** : peut s'appuyer dès maintenant sur
   la base FluxPro déjà importée (#7) et sur l'historique chargé par C8 ;
   indépendant de C10, peut être mené en parallèle.
4. **C11 — Modélisation MERISE et création de la base de travail** :
   désormais informée par les données réellement extraites et nettoyées
   (C8/C9/C10), en plus des schémas déjà connus (C2) — c'est le moment où
   le registre RGPD devient concret, avec de vraies données en main.
5. **C12 — API Omega Data** : expose la base de travail une fois peuplée.

## 6. Conséquence sur le suivi du milestone M1

Les 5 issues du milestone M1 restent celles déjà créées (#26 à #30) ; ce
document fixe uniquement l'ordre de traitement recommandé, sans imposer de
blocage strict entre elles (C9 peut par exemple être menée en parallèle de
C10). Le [plan de développement](../plan_de_developpement.md) référence ce
document pour que l'ordre retenu reste traçable avant le démarrage du
codage.
