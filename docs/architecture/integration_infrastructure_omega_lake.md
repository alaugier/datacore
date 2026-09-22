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
dupliquée par la jointure. Le mécanisme décrit en C18 §5 fonctionne donc
tel que conçu, avec l'outil retenu ici, contre des données et une base
réelles plutôt qu'un exemple jouet.

### 1.4 Portée de la décision

DuckDB sert à la fois pour les transformations internes du lake
(`raw/` → `staging/` → `curated/`, lecture CSV/JSON native, écriture
Parquet) et pour les jointures de lecture décrites en C18 §5. Ajouté aux
dépendances du projet (`requirements.txt`).

---

## 2. Ce qui reste à implémenter

- Déploiement de MinIO (service `docker-compose`) et création du bucket
  `omega-lake`.
- Scripts d'ingestion batch des 4 fichiers CSV/JSON vers `raw/`.
- Consommateur du flux SSE `/api/stream/capteurs` vers `raw/` (fenêtré
  par jour, cf. `architecture_omega_lake.md` §3).
- Scripts de transformation `raw/` → `staging/` → `curated/` (DuckDB,
  typage, Parquet).

---

## 3. Références

- [`architecture_omega_lake.md`](architecture_omega_lake.md) §3-§5 —
  zones, formats, clés de jointure conçues en C18.
- [DuckDB — PostgreSQL Extension](https://duckdb.org/docs/current/core_extensions/postgres/overview) —
  documentation officielle de `ATTACH`/`postgres`.
