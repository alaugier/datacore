# Intégration infrastructure du data lake OMEGA LAKE

**Compétence couverte : C19 — Intégrer une infrastructure de données à partir de composants**
**Épreuve associée : E7**

Ce document couvre l'intégration concrète des composants d'infrastructure
du data lake conçu en C18 ([`architecture_omega_lake.md`](architecture_omega_lake.md)).

**Avant l'implémentation** : le mécanisme technique des jointures
« curated ↔ entrepôt/staging » décrites en C18 §5 n'avait été arrêté qu'au
niveau du principe (« jointure à la lecture, pas de duplication »), pas de
l'outil concret — point explicitement soulevé en relecture externe de
C18, à trancher avant de coder plutôt qu'improvisé pipeline par pipeline.
Objet du §1 ci-dessous.

---

## 1. Mécanisme de jointure retenu : DuckDB

**Décision** : les jointures entre la zone `curated/` du lake (fichiers
Parquet) et les bases relationnelles (base de staging C11, entrepôt
OMEGA BI C13-C17) sont exécutées via **DuckDB**, en SQL, sans passer par
une bibliothèque intermédiaire type pandas.

### 1.1 Pourquoi DuckDB plutôt qu'une alternative

| Option envisagée | Écartée pour |
|---|---|
| pandas (`read_sql` + `read_parquet` + `merge`) | Charge les tables entières en mémoire avant de joindre ; pas de langage de requête, juste des appels d'API ; **introduirait une dépendance que le projet a jusqu'ici évitée** (voir §1.2) |
| Moteur big data dédié (Spark, etc.) | Déjà écarté en C18 §1 — disproportionné pour le volume réel du programme |
| Fédération de requêtes lourde (Trino/Presto) | Infrastructure à opérer en plus (cluster de workers) — contraire au principe de sobriété (`architecture_cible.md` §2.1) |
| **DuckDB** (retenu) | Bibliothèque embarquée (aucun serveur à opérer), lit les fichiers Parquet nativement, et son extension `postgres` permet d'attacher une base Postgres et de la joindre à du Parquet **dans la même requête SQL** — exactement le mécanisme décrit en C18 §5 |

### 1.2 Découverte faite en préparant cette décision : le projet n'utilise pandas nulle part

Avant de choisir l'outil, vérification de l'existant plutôt que supposé :
aucun notebook ni script du projet n'importe `pandas` — `csv`/`json` du
socle standard, `psycopg2` direct, `matplotlib` pour les graphiques
(vérifié par grep sur tous les notebooks). Introduire pandas pour ce
seul besoin aurait rompu une cohérence jusqu'ici tenue sans y avoir
pensé. DuckDB s'aligne avec cette pratique existante : requêtes SQL
directes comme le reste du projet interroge Postgres, pas une couche
DataFrame intermédiaire. Pandas reste optionnel en sortie (`.df()`)
si un notebook en a besoin pour un graphique, mais n'est jamais
nécessaire pour lire, transformer ou joindre.

### 1.3 Vérifié en conditions réelles, pas seulement documenté

Preuve de bout en bout contre les données et la base réelles du projet
(pas un exemple synthétique) :

```python
import duckdb

con = duckdb.connect()

# 1. raw/ -> curated/ : CSV source vers Parquet, DuckDB seul
con.sql("""
    COPY (SELECT * FROM read_csv_auto('data/raw/iot/capteurs_temperature.csv'))
    TO 'capteurs_temperature.parquet' (FORMAT PARQUET)
""")

# 2. Attache la vraie base de staging, en lecture seule
con.sql("INSTALL postgres; LOAD postgres;")
con.sql("""
    ATTACH 'host=localhost port=5432 dbname=datacore_staging
            user=datacore password=datacore'
    AS staging (TYPE postgres, READ_ONLY)
""")

# 3. Jointure reelle curated (Parquet) <-> staging (Postgres),
#    sur la cle entrepot -> entrepots.code (C18 §5)
con.sql("""
    SELECT e.nom, e.ville, count(*), round(avg(c.temperature_c), 2)
    FROM read_parquet('capteurs_temperature.parquet') c
    JOIN staging.public.entrepots e ON e.code = c.entrepot
    GROUP BY e.nom, e.ville
""").show()
```

Résultat obtenu contre la base de staging réelle (`docker compose`,
table `entrepots` peuplée par C11) :

| entrepôt | ville | mesures | température moyenne |
|---|---|---|---|
| Entrepot Omega Lyon | Lyon | 864 | 7,99 °C |
| Entrepot Omega Lille | Lille | 864 | 7,97 °C |
| Entrepot Omega Marseille | Marseille | 864 | 7,99 °C |

864 × 3 = 2592 mesures, cohérent avec le volume total réel de
`capteurs_temperature.csv` (vérifié en C18 §1) — aucune ligne perdue ni
dupliquée par la jointure.

**Réserve soulevée en relecture externe, à juste titre** : cette
première preuve joint Postgres à un fichier Parquet **local** — elle
démontre le mécanisme Parquet↔Postgres, pas que DuckDB sait lire un
Parquet réellement stocké dans MinIO (S3 ≠ MinIO : MinIO n'étant pas
AWS S3, l'extension `httpfs` de DuckDB a besoin d'un endpoint et d'un
style d'adressage explicites). Point vérifié séparément plutôt que
supposé équivalent — §1.3bis ci-dessous.

### 1.3bis Même preuve, cette fois avec le Parquet réellement dans MinIO

MinIO déployé (`docker compose up -d minio minio-init` — voir §4),
bucket `omega-lake` créé automatiquement au démarrage. Même script que
§1.3, avec deux différences : le Parquet est écrit et lu via `s3://`
plutôt qu'en local, et l'extension `httpfs` est configurée pour pointer
vers MinIO (pas AWS S3, qui est l'hypothèse par défaut de DuckDB) :

```python
con.sql("INSTALL httpfs; LOAD httpfs;")
con.sql("""
    SET s3_endpoint='localhost:9000';
    SET s3_access_key_id='datacore';
    SET s3_secret_access_key='datacore_lake';
    SET s3_use_ssl=false;
    SET s3_url_style='path';   -- MinIO exige le style "path", pas "virtual-hosted"
""")

con.sql("""
    COPY (SELECT * FROM read_csv_auto('data/raw/iot/capteurs_temperature.csv'))
    TO 's3://omega-lake/staging/capteurs_temperature/date=2026-08-01/part-0.parquet'
    (FORMAT PARQUET)
""")

# Jointure reelle : Parquet LU DEPUIS MINIO <-> vraie base de staging
con.sql("""
    SELECT e.nom, e.ville, count(*), round(avg(c.temperature_c), 2)
    FROM read_parquet('s3://omega-lake/staging/capteurs_temperature/date=2026-08-01/part-0.parquet') c
    JOIN staging.public.entrepots e ON e.code = c.entrepot
    GROUP BY e.nom, e.ville
""").show()
```

Résultat identique (864 mesures/site, 2592 au total) — et confirmé
persistant dans MinIO lui-même, pas seulement lisible dans la session
DuckDB qui l'a écrit (`mc ls --recursive local/omega-lake` liste bien
`staging/capteurs_temperature/date=2026-08-01/part-0.parquet`, 13 KiB).
Fichier de test supprimé après vérification (`mc rm`) — cette preuve
ne laisse pas de donnée de démonstration dans le bucket.

Le mécanisme décrit en C18 §5 est donc vérifié de bout en bout : Parquet
réellement dans MinIO, jointure réelle avec la base de staging réelle,
pas un exemple jouet à aucune étape.

### 1.4 Portée de la décision

DuckDB sert à la fois pour les transformations internes du lake
(`raw/` → `staging/` → `curated/`, lecture CSV/JSON native, écriture
Parquet) et pour les jointures de lecture décrites en C18 §5. Ajouté aux
dépendances du projet (`requirements.txt`).

---

## 2. Ingestion batch des 4 flux CSV/JSON vers `raw/`

**Décision** : l'ingestion batch (`src/datacore/storage/lake/ingestion_batch.py`)
utilise **`boto3`** (client S3 générique), pas DuckDB, pour déposer les
4 fichiers dans `raw/`.

**Pourquoi un outil différent de la jointure (§1)** : la zone `raw/`
exige une copie fidèle, octet pour octet (C18 §3). Lire un CSV/JSON avec
DuckDB puis le réécrire reformatterait potentiellement le contenu
(quotage CSV, ordre des clés JSON) sans changer l'information portée —
suffisant pour une jointure analytique, pas pour une zone dont la
garantie est « aucune transformation ». `boto3` transfère des octets
sans les interpréter ; c'est le bon outil pour ce rôle précis, DuckDB
reste réservé aux étapes où une vraie lecture structurée a lieu
(transformations `staging/`/`curated/`, jointures).

**Partitionnement** : la clé S3 porte la **date d'ingestion**
(`raw/<flux>/date=<AAAA-MM-JJ>/<fichier>`), pas une date déduite du
contenu du fichier — `capteurs_temperature.csv` couvre à lui seul le
01 au 03/08/2026 en une seule exécution, il n'y a donc pas de date
unique « du contenu » à utiliser pour cette partition. Chaque nouvelle
exécution du batch dépose un nouveau dossier `date=`, sans écraser les
précédents.

**Vérifié en conditions réelles** : script exécuté contre MinIO
réellement déployé, puis **fidélité vérifiée par somme de contrôle
SHA-256** entre chaque fichier source et l'objet déposé dans MinIO (pas
seulement « l'upload n'a pas levé d'erreur ») :

```
raw/capteurs_temperature/date=2026-09-22/capteurs_temperature.csv: OK identique
raw/geoloc_flotte/date=2026-09-22/geoloc_flotte.csv: OK identique
raw/camera_comptage/date=2026-09-22/camera_comptage.csv: OK identique
raw/rfid_scans/date=2026-09-22/rfid_scans.json: OK identique
```

Fichiers de test supprimés après vérification (`mc rm`), même discipline
qu'en §1.3bis. 4 tests unitaires (`tests/unit/test_ingestion_batch.py`)
avec un client S3 factice (aucune I/O réelle en test).

---

## 3. Consommateur du flux SSE vers `raw/`

**Décision** : le flux `/api/stream/capteurs` (non borné, 1 évènement/2s)
est mis en tampon en mémoire et **déversé par fenêtre de temps**
(`intervalle`, 5 min par défaut en production), pas seulement à la fin
de la journée — voir le docstring de
`src/datacore/storage/lake/sse_consumer.py`. Nommé
`raw/flux_sse_capteurs/`, délibérément distinct de `capteurs_temperature`
(le flux batch CSV) : le flux SSE combine température **et**
géolocalisation par évènement, ce n'est pas le même contenu malgré le
nom proche.

**Pourquoi ce n'est pas un détail** : le flux source n'est pas rejouable
(`topographie_donnees.md` §3.5) — en cas de coupure, les évènements
manqués pendant la coupure elle-même sont perdus pour de bon, aucune
API de rattrapage n'existe côté serveur. La seule variable sous
contrôle est donc la taille du tampon local non encore déposé : le
déverser par petites fenêtres plutôt qu'une fois par jour borne la
perte réelle à `intervalle`, pas à une journée entière.

### Vérifié par une coupure brutale réelle, pas seulement décrite

Point explicitement demandé en relecture externe de C19. Test mené
contre le flux SSE réel (`api-mock`) et MinIO réel, avec un intervalle
court (3 s, pour observer plusieurs dépôts en quelques secondes plutôt
que d'attendre les 5 min de production) :

1. Processus consommateur lancé en arrière-plan.
2. Après 10 s, vérification indépendante (`boto3`, hors du processus
   consommateur) : **2 fichiers déjà déposés** dans
   `raw/flux_sse_capteurs/date=2026-09-22/` (516 et 345 octets).
3. **`kill -9`** sur le processus (coupure brutale, pas un arrêt propre)
   — confirmé tué (pas de gestion de signal, donc aucune chance de
   sauvegarde de dernière minute qui fausserait la preuve).
4. Un **second** processus relancé (simule un redémarrage après crash),
   tourne 8 s, tué à son tour.
5. Vérification finale : **3 fichiers au total, 8 évènements, aucune
   collision de nom entre l'avant- et l'après-redémarrage, chaque ligne
   NDJSON relue comme un JSON valide**.

Résultat : le redémarrage ne perd que les évènements du tampon en cours
au moment du `kill` (borné par `intervalle`), jamais les fichiers déjà
déposés — le comportement attendu est vérifié en pratique, pas supposé
à partir du code seul.

**Robustesse distincte, également ajoutée** : `main()` reconnecte
automatiquement sur une coupure réseau *transitoire* (la requête HTTP
lève une exception mais le processus reste vivant) — cas différent du
crash complet testé ci-dessus. L'orchestration du processus lui-même
(relance automatique s'il s'arrête complètement) reste hors périmètre
de ce livrable.

7 tests unitaires (`tests/unit/test_sse_consumer.py`, horloge et client
S3 factices — aucune I/O réelle en test, la preuve réelle est le test
manuel ci-dessus, pas un test automatisé qui nécessiterait une vraie
infrastructure à chaque exécution de la suite).

---

## 4. État de l'implémentation

**Fait** :
- MinIO déployé (services `minio`/`minio-init` dans
  `infra/docker/docker-compose.yml`), bucket `omega-lake` créé
  automatiquement au démarrage (conteneur `minio-init`, image
  `quay.io/minio/mc`, `mc mb --ignore-existing local/omega-lake`).
  **Note pratique** : `minio/minio` et `minio/mc` ont disparu de Docker
  Hub (vérifié le 22/09/2026, `pull access denied`) — remplacés par
  `quay.io/minio/minio` et `quay.io/minio/mc`, le registre désormais
  recommandé par l'éditeur.
- Variables d'environnement ajoutées (`.env.example`,
  `src/datacore/config.py`) : `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`,
  `MINIO_API_PORT`/`MINIO_CONSOLE_PORT`, `OMEGA_LAKE_BUCKET`,
  `OMEGA_LAKE_S3_ENDPOINT`.
- Mécanisme de jointure DuckDB↔MinIO↔Postgres vérifié en conditions
  réelles (§1.3bis).
- Ingestion batch des 4 flux CSV/JSON vers `raw/` (§2), fidélité
  vérifiée par somme de contrôle.
- Consommateur du flux SSE vers `raw/` (§3), robustesse au crash vérifiée
  en conditions réelles.

**Reste à faire** :
- Scripts de transformation `raw/` → `staging/` → `curated/` (DuckDB,
  typage, Parquet) — réutiliseront le mécanisme vérifié en §1.3bis.

---

## 5. Références

- [`architecture_omega_lake.md`](architecture_omega_lake.md) §3-§5 —
  zones, formats, clés de jointure conçues en C18.
- [DuckDB — PostgreSQL Extension](https://duckdb.org/docs/current/core_extensions/postgres/overview) —
  documentation officielle de `ATTACH`/`postgres`.
