# Script de démo live, minuté — issue #98

**Compétence couverte : démonstration du pipeline en conditions réelles, à l'oral.**
**Emplacement dans la trame** : répartie sur **6 moments live**, chacun à la
slide qui en parle déjà, plutôt qu'un seul bloc en début de deck
([`slides/slides.md`](../../slides/slides.md)) — décidé après relecture
de la v1 de ce script (bloc unique à C8) : Swagger/Adminer/Grafana/MinIO/
pseudonymisation n'ont rien à voir avec « automatiser l'extraction » (C8), et un bloc
unique est un point de défaillance unique si quelque chose coince. Toutes
les commandes ci-dessous ont été exécutées et vérifiées réellement avant
l'oral (pas de commande non testée) — voir
[`chapitre 5 §6.5 du rapport`](../latex/chapitres/05_m4_restitution_bi.tex)
pour les commandes manuelles équivalentes (le DAG Airflow les appelle telles
quelles, sans les réécrire).

**Préparation, ~10 minutes avant l'oral** (hors chronométrage ci-dessous) :

```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env build
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d
docker compose -f infra/docker/docker-compose.yml --env-file .env --profile airflow build
docker compose -f infra/docker/docker-compose.yml --env-file .env --profile airflow up -d
```

**Pourquoi reconstruire systématiquement, pas seulement `up -d`** (leçon tirée
d'un échec réel du déclenchement Airflow le 19/11/2026, en conditions de
soutenance) : `api-mock`, `omega-data-api`, `alerting-webhook` et `airflow`
sont les 4 services `build:` du `docker-compose.yml` — leur code est copié
dans l'image **au moment du build**, pas monté en direct depuis le dépôt.
Une image construite avant une modification du code (ex. une nouvelle
migration Alembic) continue de tourner avec l'ancien code tant qu'elle
n'est pas reconstruite, même après un `docker compose up -d` — `up -d`
réutilise une image existante, il ne la reconstruit pas. Symptôme observé
concrètement : la base Postgres partagée avait été mise à jour jusqu'à la
migration `bd4f2d68682a` (via l'environnement hôte), mais l'image Airflow,
construite la veille, ne la connaissait pas encore →
`alembic upgrade head` échouait avec `Can't locate revision identified by
'bd4f2d68682a'`. `docker compose build` avant chaque session (coût : quelques
secondes si rien n'a changé, grâce au cache de build) élimine cette classe
de bug par construction, plutôt que de compter sur le réflexe de s'en
souvenir.

Vérifier que tout est sain avant d'entrer en salle :
```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env ps
docker compose -f infra/docker/docker-compose.yml --env-file .env --profile airflow ps
```
Onglets navigateur à ouvrir à l'avance (dans cet ordre d'apparition dans le
deck) : `localhost:8000/docs` (Swagger),
`localhost:8081/?pgsql=db&username=datacore&db=datacore_staging` (Adminer —
système/serveur/utilisateur/base déjà pré-remplis via l'URL, pas l'URL nue),
`localhost:9001` (MinIO), `localhost:3000` (Grafana), `localhost:8080`
(Airflow) — tous déjà connectés. Chaque lien est désormais cliquable
directement depuis la note « → Démo live à ce point » en bas de la slide
concernée (ouvre dans un nouvel onglet) — plus besoin de retrouver le port
de tête.

---

## Les 6 moments live, dans l'ordre du deck

### 1. Slide « C12 — Documentation interactive (Swagger) » (~30-45s)

**Depuis le 19/11/2026** (voir
[`evolution_authentification_jwt.md`](evolution_authentification_jwt.md)) :
authentification par JWT, pas par clé API directe — un pas
supplémentaire par rapport à l'oral du 19/11, à annoncer si le jury l'a
déjà vu autrement : « j'ai renforcé l'authentification depuis la
soutenance, voici le même scénario avec le nouveau mécanisme ».

Onglet Swagger (`localhost:8000/docs`) : bouton **Authorize**, champ
**username** = `omega-data-analyst-2026`, champ **password** laissé
vide, bouton **Authorize** (dans la pop-up) — statut passe à
"Authorized". Puis **Try it out** sur `GET /kpis/taux-service`, Execute.

« L'API expose un KPI métier — taux de service par client, généré
automatiquement par FastAPI, pas écrit à la main. L'authentification
passe maintenant par un jeton JWT, obtenu ici en échangeant ma clé. »

**Preuve 403** (slide dédiée juste après celle-ci, avec la capture en
secours) : ré-ouvrir **Authorize**, **Logout** d'abord, puis username =
`omega-norddrive-2026`, password vide, Authorize. Puis **Try it out**
sur `GET /commandes-clients/{commande_client_id}/lignes` avec
`commande_client_id=467` (une commande FreshMarket), **Execute** —
réponse `403 {"detail": "Hors de votre périmètre client"}`. Vérifié en
conditions réelles le 19/11/2026 (`curl` direct et interface Swagger
réelle, voir `docs/architecture/registre_rgpd.md` §4 pour le modèle
d'accès).

« Pas juste une restriction en liste — une demande précise sur la
commande d'un autre client est explicitement refusée, pas seulement
filtrée. »

### 2. Slide « C11 / C14 — Les deux bases en conditions réelles (Adminer) » (~20-30s)

Le lien de la slide ouvre
`localhost:8081/?pgsql=db&username=datacore&db=datacore_staging` : Système,
Serveur, Utilisateur et Base déjà pré-remplis (paramètres d'URL Adminer).
**Important** : Adminer n'accepte jamais le mot de passe par URL (sécurité) —
taper `datacore` dans le champ Mot de passe, puis **Authentification**. Ne
pas se contenter d'ouvrir `localhost:8081` à la main : le système par
défaut d'Adminer est MySQL/MariaDB, pas PostgreSQL, et la connexion échoue
(« Connection refused ») si on oublie de le changer — repéré lors d'une
répétition, corrigé en passant par l'URL plutôt que par la sélection
manuelle du menu déroulant. Une fois connecté, basculer sur
`datacore_omega_bi` via le menu **DB** en haut à gauche, puis cliquer
**select clients** pour montrer des valeurs de champs réelles, pas
seulement la liste des tables.

« Même principe que DBeaver, mais 100 % navigateur — pratique pour montrer
rapidement le contenu d'une base sans changer d'outil. »

### 3. Slide « C19 — MinIO en conditions réelles » (~20-30s)

Onglet MinIO (`localhost:9001`), bucket `omega-lake`, montrer les préfixes
`raw/`, `staging/`, `curated/`, `curated_bi/`.

« Le data lake suit la même convention de zones que le rapport décrit —
infrastructure réelle, pas une maquette. »

### 4. Slide « C21 — Gouvernance : le parcours de la pseudonymisation » (~45s), après avoir déroulé les 5 étapes

Terminal, requête DuckDB pseudonymisée :

```bash
python3 -c "
import duckdb
con = duckdb.connect()
con.sql(\"INSTALL httpfs; LOAD httpfs;\")
con.sql(\"\"\"
    SET s3_endpoint='localhost:9000';
    SET s3_access_key_id='lake_reader';
    SET s3_secret_access_key='datacore_lake_reader';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
\"\"\")
print(con.sql(\"SELECT vehicule_id, timestamp, lat, lon FROM read_parquet('s3://omega-lake/curated_bi/geoloc_flotte/part-0.parquet') LIMIT 5\"))
"
```

« Et la preuve que ça fonctionne : `vehicule_id` est un hash, pas
l'identifiant réel, dans l'export BI — avec les identifiants `lake_reader`,
en lecture seule, jamais les identifiants admin MinIO. »

Si le jury demande à voir l'identifiant réel pour comparer : la même
requête sur `curated/geoloc_flotte/part-0.parquet` (sans `_bi`) montre
`VH-001`, etc., en clair — zone interne, jamais exposée à `lake_reader`.

### 5. Slide « C16bis — Restitution OMEGA BI » (~20-30s)

Onglet Grafana (`localhost:3000`), dashboard SLA OMEGA BI déjà ouvert.

« Même type de donnée, vue BI — taux de service, délai moyen, stock
disponible, les trois chiffres déjà cités sur la slide. »

### 6. Slide « Airflow — orchestration (stretch goal) » (~30s), en toute fin de deck

Onglet Airflow (`localhost:8080`) déjà ouvert — cliquer **Trigger** sur
`datacore_pipeline`.

« On déclenche le pipeline complet en direct — staging, entrepôt, data
lake, 12 tâches. » Pendant l'exécution (~20-25s réels, vue Grid),
commenter les 3 groupes qui passent au vert : `staging_c8_c11` (dont
`reset_staging` en tête, pour que ce soit rejouable à l'identique),
`entrepot_omega_bi_c13_c15`, `data_lake_omega_lake_c18_c21`. « Douze
tâches réussies — c'est tout le pipeline présenté depuis le début de
l'oral, rejoué en 25 secondes. »

**C'est délibérément le seul endroit du deck où le DAG est déclenché** —
pas en avance à C8 : le déclenchement et l'explication de l'orchestration
restent au même moment, pas séparés de plusieurs dizaines de minutes.

---

## Plan de repli

Chaque étape a une capture d'écran déjà en secours, affichée sur la slide
elle-même dans [`slides/slides.md`](../../slides/slides.md) (pas besoin
d'aller la chercher ailleurs) : `swagger_omega_data_api.png`,
`adminer_staging_tables.png` + `adminer_entrepot_tables.png`,
`gestion_operationnelle_omega_bi_dashboard_grafana.png`,
`minio_console_buckets.png`, `airflow_dag_run_success.png`. Annoncer
simplement : « Je vous montre la capture, l'environnement réel est
disponible après la soutenance si vous voulez le reprendre en main. »

Si Airflow lui-même est injoignable (cas le plus grave, en toute fin de
deck) : repli sur les commandes manuelles du
[chapitre 5 §6.5 du rapport](../latex/chapitres/05_m4_restitution_bi.tex)
— ce sont exactement les mêmes commandes que celles appelées par
[`infra/airflow/dags/datacore_pipeline.py`](../../infra/airflow/dags/datacore_pipeline.py)
(aucune divergence possible, le DAG ne fait qu'appeler ces scripts tels
quels), seulement tapées une par une au lieu d'être orchestrées. Dans ce
cas, prévenir le jury avant de commencer : « Un souci réseau empêche
l'interface Airflow, je vous montre les mêmes étapes en ligne de
commande. »

## Si le jury veut creuser davantage les bases (au-delà d'Adminer)

Adminer (moment 2 ci-dessus) couvre déjà la démo par défaut. Si le jury
demande un outil plus complet (éditeur SQL avancé, export, comparaison de
schémas) :

- **DBeaver sous Windows**, connecté à `localhost:5432` — WSL2 redirige
  `localhost` entre Windows et WSL2 automatiquement, aucune
  configuration réseau supplémentaire nécessaire. Deux connexions
  distinctes et nommées (`DATA CORE — Staging`, base
  `datacore_staging` ; `DATA CORE — Entrepôt OMEGA BI`, base
  `datacore_omega_bi`), mêmes identifiants (`datacore`/`datacore`).

## Si une question très technique porte sur « ce qui s'exécute réellement »

Les commandes du chapitre 5 §6.5 sont la référence lisible ; le fichier
[`infra/airflow/dags/datacore_pipeline.py`](../../infra/airflow/dags/datacore_pipeline.py)
les contient identiques, dans les `bash_command=` de chaque tâche — ce
n'est pas une réécriture, juste un appel direct. Pointer l'un ou l'autre
selon ce que le jury demande à voir (la commande elle-même, ou comment
elle est orchestrée).
