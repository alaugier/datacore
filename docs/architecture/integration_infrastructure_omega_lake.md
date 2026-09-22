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

MinIO déployé (`docker compose up -d minio minio-init` — voir §2),
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

## 2. État de l'implémentation

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

**Reste à faire** :
- Scripts d'ingestion batch des 4 fichiers CSV/JSON vers `raw/`.
- Consommateur du flux SSE `/api/stream/capteurs` vers `raw/` (fenêtré
  par jour, cf. `architecture_omega_lake.md` §3).
- Scripts de transformation `raw/` → `staging/` → `curated/` (DuckDB,
  typage, Parquet) — réutiliseront le mécanisme vérifié en §1.3bis.

---

## 3. Références

- [`architecture_omega_lake.md`](architecture_omega_lake.md) §3-§5 —
  zones, formats, clés de jointure conçues en C18.
- [DuckDB — PostgreSQL Extension](https://duckdb.org/docs/current/core_extensions/postgres/overview) —
  documentation officielle de `ATTACH`/`postgres`.
