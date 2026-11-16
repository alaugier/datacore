# Script de démo live, minuté — issue #98

**Compétence couverte : démonstration du pipeline en conditions réelles, à l'oral.**
**Emplacement dans la trame** : un seul moment live, à la slide « C8 — Automatiser
l'extraction » (Bloc 2, [`slides/slides.md`](../../slides/slides.md), ~15' au
total pour le bloc). Toutes les commandes ci-dessous ont été exécutées et
vérifiées réellement avant l'oral (pas de commande non testée) — voir
[`chapitre 5 §6.5 du rapport`](../latex/chapitres/05_m4_restitution_bi.tex)
pour les commandes manuelles équivalentes (le DAG Airflow les appelle telles
quelles, sans les réécrire).

**Préparation, ~10 minutes avant l'oral** (hors chronométrage ci-dessous) :

```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d
docker compose -f infra/docker/docker-compose.yml --env-file .env --profile airflow up -d
```

Vérifier que tout est sain avant d'entrer en salle :
```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env ps
docker compose -f infra/docker/docker-compose.yml --env-file .env --profile airflow ps
```
Onglets navigateur à ouvrir à l'avance : `localhost:8080` (Airflow, déjà
connecté), `localhost:8000/docs` (Swagger), `localhost:3000` (Grafana, déjà
connecté), `localhost:9001` (console MinIO, déjà connectée).

---

## Déroulé minuté (~3min30, pendant la slide C8)

| T+ | Action | Ce qui se dit |
|---|---|---|
| 0:00 | Onglet Airflow (`localhost:8080`) déjà ouvert — cliquer **Trigger** sur `datacore_pipeline` | « On déclenche le pipeline complet en direct — staging, entrepôt, data lake, 12 tâches. » |
| 0:00–0:30 | Pendant l'exécution (~20-25s réels, vue Grid), commenter les 3 groupes qui passent au vert : `staging_c8_c11` (dont `reset_staging` en tête, pour que ce soit rejouable à l'identique), `entrepot_omega_bi_c13_c15`, `data_lake_omega_lake_c18_c21` | « Trois groupes, dans l'ordre réel de dépendance des données — staging d'abord, puis l'entrepôt qui en dépend, puis le data lake. » |
| 0:30 | 12/12 tâches en succès affiché | « C'est fait — on va vérifier le résultat à trois endroits. » |
| 0:30–1:15 | Onglet Swagger (`localhost:8000/docs`) — bouton **Authorize**, coller `omega-data-analyst-2026`, puis **Try it out** sur `GET /kpis/taux-service`, Execute | « L'API expose un KPI métier — taux de service par client, recalculé sur les données qu'on vient de recharger. » |
| 1:15–2:00 | Onglet Grafana (`localhost:3000`), dashboard SLA OMEGA BI | « Même donnée, vue BI — le dashboard est à jour avec le run qu'on vient de lancer. » |
| 2:00–2:45 | Onglet MinIO (`localhost:9001`), bucket `omega-lake`, montrer les préfixes `raw/`, `staging/`, `curated/`, `curated_bi/` | « Le data lake suit la même convention de zones que le rapport décrit — rien de cosmétique, c'est ce qui vient d'être écrit à l'instant. » |
| 2:45–3:30 | Terminal, requête DuckDB pseudonymisée (commande ci-dessous) | « Et la preuve que la pseudonymisation fonctionne : `vehicule_id` est un hash, pas l'identifiant réel, dans l'export BI. » |
| 3:30 | Retour aux slides, enchaîner sur C9 | — |

### Commande de la requête pseudonymisée (T+2:45)

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

Identifiants `lake_reader` (lecture seule, jamais les identifiants admin
MinIO) — cohérent avec les droits d'accès par groupe décrits en C21. Si le
jury demande à voir l'identifiant réel pour comparer : la même requête sur
`curated/geoloc_flotte/part-0.parquet` (sans `_bi`) montre `VH-001`, etc.,
en clair — zone interne, jamais exposée à `lake_reader`.

---

## Plan de repli

Chaque étape a une capture d'écran déjà en secours dans
[`slides/public/images/`](../../slides/public/images/) si un outil est
injoignable le jour J (Wi-Fi, projecteur, service qui ne redémarre pas) :
`swagger_omega_data_api.png`, `gestion_operationnelle_omega_bi_dashboard_grafana.png`,
`minio_console_buckets.png`. Annoncer simplement : « Je vous montre la
capture, l'environnement réel est disponible après la soutenance si vous
voulez le reprendre en main. »

Si Airflow lui-même est injoignable (cas le plus grave, bloque toute la
démo) : repli sur les commandes manuelles du
[chapitre 5 §6.5 du rapport](../latex/chapitres/05_m4_restitution_bi.tex)
— ce sont exactement les mêmes commandes que celles appelées par
[`infra/airflow/dags/datacore_pipeline.py`](../../infra/airflow/dags/datacore_pipeline.py)
(aucune divergence possible, le DAG ne fait qu'appeler ces scripts tels
quels), seulement tapées une par une au lieu d'être orchestrées. Dans ce
cas, prévenir le jury avant de commencer : « Un souci réseau empêche
l'interface Airflow, je vous montre les mêmes étapes en ligne de
commande. »

## Si une question très technique porte sur « ce qui s'exécute réellement »

Les commandes du chapitre 5 §6.5 sont la référence lisible ; le fichier
[`infra/airflow/dags/datacore_pipeline.py`](../../infra/airflow/dags/datacore_pipeline.py)
les contient identiques, dans les `bash_command=` de chaque tâche — ce
n'est pas une réécriture, juste un appel direct. Pointer l'un ou l'autre
selon ce que le jury demande à voir (la commande elle-même, ou comment
elle est orchestrée).
