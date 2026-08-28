# Création de l'entrepôt OMEGA BI

**Compétence couverte : C14 — Créer un entrepôt de données**
**Épreuve associée : E5**

Ce document décrit la création physique de l'entrepôt « OMEGA BI »,
implémentant la modélisation étoile/flocon conçue en C13
(`docs/architecture/modelisation_omega_bi.md`) : architecture retenue,
procédure d'installation, accès configurés, et procédure de test.

---

## 1. Architecture physique

L'entrepôt vit dans une **base Postgres distincte** (`datacore_omega_bi`)
de la base de staging (`datacore_staging`), mais sur la **même instance
Postgres** que celle-ci (conteneur `db` de
`infra/docker/docker-compose.yml`) — cohérent avec le principe de
sobriété RGESN déjà retenu ailleurs dans le programme : pas de second
conteneur pour une séparation qui n'a besoin d'être que logique.

À l'intérieur de cette base, **3 schémas Postgres** rendent tangible
l'approche bottom-up par datamarts à dimensions conformées décrite en
C13 §1 :

| Schéma Postgres | Contenu | Rôle |
|---|---|---|
| `dimensions` | `dim_client`, `dim_site`, `dim_produit`, `dim_categorie`, `dim_temps`, `dim_transporteur` | Dimensions conformées, partagées par les deux datamarts |
| `exploitation` | `fait_expedition`, `fait_stock` | Datamart Exploitation |
| `commercial` | `fait_commande` | Datamart Commercial |

Les tables de faits référencent les dimensions par clé étrangère
inter-schéma (ex. `exploitation.fait_expedition.client_key` →
`dimensions.dim_client.client_key`) — Postgres l'autorise nativement,
pas de contrainte technique à contourner.

Schéma SQLAlchemy : [`src/datacore/storage/warehouse/models.py`](../../src/datacore/storage/warehouse/models.py).
Migration Alembic : [`src/datacore/storage/warehouse/migrations/versions/`](../../src/datacore/storage/warehouse/migrations/versions/).

**`Dim_Client` ne porte pas encore les colonnes SCD2** (`valid_from`,
`valid_to`, `is_current`) : elles seront ajoutées par une migration
Alembic additionnelle en C17, conformément au choix déjà documenté en
C13 §6.1.

---

## 2. Procédure d'installation

Prérequis : `docker compose -f infra/docker/docker-compose.yml up -d db`
(le service `db` héberge déjà la base de staging ; l'entrepôt y ajoute
une seconde base sur la même instance).

```bash
# 1. Créer la base datacore_omega_bi et le rôle de lecture seule bi_reader
./scripts/init_omega_bi_db.sh

# 2. Créer les 3 schémas et les 9 tables (+ accorder les lectures à bi_reader)
alembic -c alembic_omega_bi.ini upgrade head

# 3. Charger la dimension calendaire (générée, pas de source -- voir §3)
python3 -m datacore.storage.warehouse.load_dim_temps
```

À ce stade, l'entrepôt est créé et prêt à être peuplé par le pipeline
ETL (C15) — aucune donnée de fait n'est chargée par cette procédure,
seule `dim_temps` (dimension générée) l'est.

**Alembic distinct de la base de staging** : `alembic_omega_bi.ini`
(script_location dédié) plutôt qu'un ajout à `alembic.ini` — deux bases
Postgres séparées, donc deux historiques de migration indépendants, sur
le même principe qu'un DSN dédié
(`datacore.ingestion.config.OMEGA_BI_DB_DSN`, à côté de
`STAGING_DB_DSN`).

---

## 3. `Dim_Temps` : dimension générée, pas chargée depuis une source

Contrairement aux autres dimensions (issues de tables FluxPro/TransFlow,
chargées par C15), `Dim_Temps` n'a pas de source de données propre —
pratique Kimball standard. `load_dim_temps.py` la génère
programmatiquement du 2022-01-01 au 2027-12-31 (borne basse : date la
plus ancienne observée dans le jeu de données, vérifiée empiriquement ;
borne haute : marge après la fin du programme, voir
`feuille_de_route.md`). Idempotent (`ON CONFLICT (date_key) DO
NOTHING`), rejouable sans dupliquer.

---

## 4. Accès configurés

Rôle Postgres `bi_reader` (créé par `scripts/init_omega_bi_db.sh`),
lecture seule sur les 3 schémas :

```sql
GRANT USAGE ON SCHEMA <schema> TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA <schema> TO bi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA <schema> GRANT SELECT ON TABLES TO bi_reader;
```

Ces trois instructions sont exécutées dans la migration Alembic
elle-même (pas dans le script d'installation) : le `ALTER DEFAULT
PRIVILEGES` garantit que les tables créées par de futures migrations
(ex. les colonnes SCD2 ajoutées en C17 ne changent rien ici, mais une
future table supplémentaire serait automatiquement couverte) restent
accessibles à `bi_reader` sans regrant manuel.

Ce rôle correspond à l'usage « Data Analysts : lecture sur entrepôt
OMEGA BI (datamarts), sans besoin d'accéder aux données brutes » déjà
identifié dans `architecture_cible.md` §4 (mise en conformité RGPD,
matrice des accès). Une
gestion d'accès plus fine (par datamart, par groupe métier) n'est pas
nécessaire à ce stade : les 3 schémas ne contiennent aucune donnée
personnelle (voir C13 §6.5, §8) — le point de vigilance RGPD pour
l'entrepôt porte sur la procédure de purge d'un `Dim_Client` historisé
après C17, traité en C16, pas sur un accès différencié aujourd'hui.

---

## 5. Procédure de test

**Tests unitaires** (`tests/unit/test_load_dim_temps.py`) : logique pure
de génération du calendrier (`generer_lignes`) — couverture de plage,
format `date_key` (YYYYMMDD), attributs dérivés (année/trimestre/mois),
calcul `est_weekend` ; et `charger_dim_temps` avec une connexion/curseur
factices (SQL émis, `ON CONFLICT`, commit). Aucune dépendance à une
vraie base — cohérent avec le reste de la CI (`.github/workflows/ci.yml`
ne provisionne pas de service Postgres).

**Test de bout en bout manuel** (Docker Compose), effectué lors de la
création de ce livrable :

```bash
docker compose -f infra/docker/docker-compose.yml up -d db
./scripts/init_omega_bi_db.sh
alembic -c alembic_omega_bi.ini upgrade head
python3 -m datacore.storage.warehouse.load_dim_temps
```

Vérifié pour de vrai :
- `\dn` sur `datacore_omega_bi` : les 3 schémas (`dimensions`,
  `exploitation`, `commercial`) existent.
- `\dt` sur chacun : les 6 + 2 + 1 = 9 tables attendues sont présentes,
  au bon endroit.
- `\dp dimensions.dim_client` : `bi_reader=r/datacore` confirmé (lecture
  seule accordée).
- `alembic downgrade base` : les 3 schémas disparaissent proprement
  (`DROP SCHEMA ... CASCADE`), puis `alembic upgrade head` recrée tout
  à l'identique — cycle complet testé, pas seulement la création.
- `load_dim_temps` : 2191 lignes envoyées (2022-01-01 à 2027-12-31),
  rejouable sans doublon (relancé deux fois, count final inchangé à
  2191) ; ligne `2026-08-28` vérifiée individuellement (`date_key =
  20260828`, `jour_semaine = 5`, `est_weekend = false` — vendredi,
  correct).

---

## 6. Références

- [`modelisation_omega_bi.md`](modelisation_omega_bi.md) — modélisation
  étoile/flocon implémentée ici (C13).
- [`sequencement_bloc3.md`](sequencement_bloc3.md) — ordre de traitement
  du Bloc 3.
- [`modelisation_merise.md`](modelisation_merise.md) — base de staging,
  source des futurs chargements ETL (C15).
