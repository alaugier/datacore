# Index du code par compétence — préparation à l'oral

Objectif : pour chaque compétence, savoir en quelques secondes **quel
fichier ouvrir**, **quelle fonction montrer**, et **quoi dire
dessus** — pour répondre à « montrez-nous le bout de code qui fait
X ». Ce n'est pas un résumé à lire, c'est une carte de navigation :
s'entraîner à ouvrir chaque fichier cité et à relire la fonction
indiquée directement dans l'éditeur, pas seulement ce document. Tous
les chemins sont des liens cliquables (relatifs à la racine du
dépôt) -- fonctionnent dans l'aperçu GitHub comme dans la plupart des
éditeurs qui rendent le Markdown.

**Périmètre** : chaque entrée de ce document pointe vers un objet
concret de programmation -- script, classe, fonction/méthode, variable
d'environnement, fichier de configuration, ou commande
Python/Docker/shell. Les questions de jugement sans objet technique
précis (performance, passage à l'échelle, choix d'architecture
argumentés, écarts cahier des charges) n'ont pas leur place ici --
elles vivent dans
[`synthese_technique_oral.md` §3](synthese_technique_oral.md#3-anticipation-qa-jury--points-sensibles)
(anticipation Q&A jury, issue #96).

Les compétences C1, C4-C7 n'ont pas de code associé (livrables
documentaires) — indiqué explicitement pour ne pas chercher un script
qui n'existe pas.

---

## Bloc 1 — Cadrage (documentaire, pas de code)

| C | Document à montrer |
|---|---|
| C1 | [`docs/architecture/etude_faisabilite.md`](etude_faisabilite.md) (entretiens, RICE §6, SMART §7) |
| C2 | [`docs/architecture/topographie_donnees.md`](topographie_donnees.md) (glossaire §1, cartographie des sources §2) |
| C3 | [`docs/architecture/architecture_cible.md`](architecture_cible.md) (AS IS/TO BE §1-2) |
| C4 | [`docs/architecture/veille_technique_reglementaire.md`](veille_technique_reglementaire.md) |
| C5 | [`docs/architecture/feuille_de_route.md`](feuille_de_route.md) (Gantt/PERT Mermaid §4) |
| C6 | [`docs/architecture/supervision_projet.md`](supervision_projet.md) |
| C7 | [`docs/architecture/communication_lancement.md`](communication_lancement.md) |

---

## Bloc 2 — Collecte & Stockage (C8-C12)

**C8 — Automatiser l'extraction** : [`src/datacore/ingestion/`](../../src/datacore/ingestion/)
- [`run_extraction.py`](../../src/datacore/ingestion/run_extraction.py) — orchestrateur, appelle les 5 connecteurs dans l'ordre.
- [`fluxpro.py`](../../src/datacore/ingestion/fluxpro.py) / [`transflow.py`](../../src/datacore/ingestion/transflow.py) — requêtes SQL directes / appels API REST (`requests`).
- [`portail_scraping.py`](../../src/datacore/ingestion/portail_scraping.py) — `scrape_colis_list()`/`scrape_colis_detail()` : scraping HTML (pas d'API côté portail transporteur), à montrer si la question porte spécifiquement sur le scraping. Le portail scrapé est lui-même simulé par `api-mock` (voir § dédié plus bas).
- [`clients_files.py`](../../src/datacore/ingestion/clients_files.py) — `read_norddrive()`/`read_freshmarket()`/`read_mediotex()` : un lecteur par format hétérogène.
- [`landing.py`](../../src/datacore/ingestion/landing.py) — écrit dans `data/interim/` (zone d'atterrissage, non versionnée).

**C9 — Requêtes SQL d'extraction** : [`sql/extraction/01_commandes_par_client_periode.sql`](../../sql/extraction/01_commandes_par_client_periode.sql) → [`05_evolution_delai_historique_par_annee.sql`](../../sql/extraction/05_evolution_delai_historique_par_annee.sql) (5 fichiers SQL bruts, pas de code Python ici) + [`scripts/load_historique.sh`](../../scripts/load_historique.sh). Résultats réels documentés dans [`docs/architecture/requetes_sql_extraction.md`](requetes_sql_extraction.md).

**C10 — Agrégation/dédoublonnage** : [`src/datacore/processing/`](../../src/datacore/processing/)
- [`clients_cleaning.py`](../../src/datacore/processing/clients_cleaning.py) — fonction `deduplicate()` : dédoublonnage au grain (commande, produit). **Déjà dans le rapport, chapitre 2 §C10.**
- [`run_cleaning.py`](../../src/datacore/processing/run_cleaning.py) — orchestrateur, écrit `data/interim/clients_consolidated.json`.

**C11 — Créer une base de données** : [`src/datacore/storage/staging/`](../../src/datacore/storage/staging/)
- [`models.py`](../../src/datacore/storage/staging/models.py) — définitions SQLAlchemy Core des tables (`tracking_number` sans FK, clé métier). **Déjà dans le rapport.**
- [`migrations/versions/`](../../src/datacore/storage/staging/migrations/versions/) — historique Alembic (base de staging).
- [`load_staging.py`](../../src/datacore/storage/staging/load_staging.py) — `main()` : transaction unique, voir chapitre 5 §6.5.1 du rapport.

**C12 — Partager le jeu de données** : [`src/datacore/api/`](../../src/datacore/api/)
- [`main.py`](../../src/datacore/api/main.py) — routes FastAPI.
- [`auth.py`](../../src/datacore/api/auth.py) — `get_current_principal()` + `_resolve_client_scope()` : un référent client qui demande un autre client est **silencieusement ramené** à son périmètre, pas juste rejeté. **Déjà dans le rapport (diagramme de séquence).**
- [`db.py`](../../src/datacore/api/db.py) — une connexion Postgres par requête (dépendance FastAPI), fermée en `finally` ; pas de pool — à mentionner si on demande pourquoi.
- [`repository.py`](../../src/datacore/api/repository.py) / [`schemas.py`](../../src/datacore/api/schemas.py) — accès SQL / modèles Pydantic (→ spec OpenAPI auto-générée).

---

## Bloc 3 — Entrepôt OMEGA BI (C13-C17)

**C13 — Modéliser un entrepôt** : pas de code d'exécution (compétence de conception) — [`docs/architecture/modelisation_omega_bi.md`](modelisation_omega_bi.md) (matrice de bus §2, MCD §4, le texte "pourquoi pas de `Fait_Livraison`" juste avant §5.2). Le schéma physique qui en découle est en C14.

**C14 — Créer un entrepôt** : [`scripts/init_omega_bi_db.sh`](../../scripts/init_omega_bi_db.sh) (base + rôle `bi_reader`) + [`alembic_omega_bi.ini`](../../alembic_omega_bi.ini) + [`src/datacore/storage/warehouse/models.py`](../../src/datacore/storage/warehouse/models.py) (3 schémas à la création) + [`migrations/versions/`](../../src/datacore/storage/warehouse/migrations/versions/) (5 fichiers notables : [`87dcc1313f23`](../../src/datacore/storage/warehouse/migrations/versions/87dcc1313f23_create_warehouse_schemas_dimensions_.py) schéma initial, [`ad009b506239`](../../src/datacore/storage/warehouse/migrations/versions/ad009b506239_add_scd2_columns_to_dim_client.py) colonnes SCD2 C17, [`44a800999124`](../../src/datacore/storage/warehouse/migrations/versions/44a800999124_add_partial_unique_index_enforcing_one_.py) index unique `uq_dim_client_courant`, [`f6242611380a`](../../src/datacore/storage/warehouse/migrations/versions/f6242611380a_add_gouvernance_schema_journal_.py) schéma `gouvernance` C16, [`a487cd05b8d5`](../../src/datacore/storage/warehouse/migrations/versions/a487cd05b8d5_add_monitoring_schema_for_lake_.py) schéma `monitoring` M4).

**C15 — Pipelines ETL** : [`src/datacore/storage/warehouse/load_warehouse.py`](../../src/datacore/storage/warehouse/load_warehouse.py)
- `_run()` — orchestration complète : `truncate_warehouse()` puis chargement des 6 dimensions, puis des 3 faits, puis `commit()`. **Déjà dans le rapport (chapitre 5 §6.5.1, transaction unique).**
- `load_fait_expedition_historique()` — la logique de quarantaine (lignes non rapprochées mises de côté, pas rejetées silencieusement) : bon exemple si la question porte sur la qualité des données en sortie d'ETL.

**C16 — Gestion opérationnelle** : [`src/datacore/governance/`](../../src/datacore/governance/)
- [`journal.py`](../../src/datacore/governance/journal.py) — `journaliser()` : context manager, connexion Postgres séparée du chargement, commit immédiat du statut `en_cours`. **Déjà dans le rapport (pourquoi une connexion séparée).**
- [`audit_rgpd.py`](../../src/datacore/governance/audit_rgpd.py) — `auditer()` : scanne les noms de colonnes de l'entrepôt à la recherche de motifs de données personnelles (`colonnes_suspectes()`), audit automatisé plutôt que déclaratif.
- [`scripts/backup_omega_bi.sh`](../../scripts/backup_omega_bi.sh) — sauvegarde partielle/complète planifiée.

**C17 — SCD2** : [`src/datacore/storage/warehouse/load_warehouse.py`](../../src/datacore/storage/warehouse/load_warehouse.py), fonction `load_dim_client()`. **Déjà entièrement dans le rapport** (listing + explication de `r`/`current`/`mapping`, chapitre 3 §C17) — relire ce listing avant l'oral, c'est probablement la fonction la plus technique à défendre.

---

## Bloc 4 — Data Lake OMEGA LAKE (C18-C21)

**C18 — Architecture du data lake** : [`docs/architecture/architecture_omega_lake.md`](architecture_omega_lake.md) (schema-on-read §1) + [`docs/architecture/organisation_omega_lake.md`](organisation_omega_lake.md) (hiérarchie bucket→zone→flux→objet) + [`src/datacore/storage/lake/transform.py`](../../src/datacore/storage/lake/transform.py) pour la jointure DuckDB/`httpfs` réelle (configuration déjà dans le rapport, chapitre 4).

**C19 — Intégration infrastructure** : [`src/datacore/storage/lake/`](../../src/datacore/storage/lake/)
- [`ingestion_batch.py`](../../src/datacore/storage/lake/ingestion_batch.py) — `ingerer_flux_batch()` : dépôt `boto3` des 4 flux IoT batch dans `raw/`, copie fidèle octet pour octet.
- [`sse_consumer.py`](../../src/datacore/storage/lake/sse_consumer.py) — consommateur du flux temps réel, fenêtré par intervalle de 5 minutes ; testé par coupure brutale réelle (`kill -9`). Processus continu, pas un script à exécution unique — à préciser si on vous demande de le lancer en direct. Le flux consommé est généré aléatoirement par `api-mock` (voir § dédié plus bas), pas par de vrais capteurs.
- [`transform.py`](../../src/datacore/storage/lake/transform.py) — jointure DuckDB `raw/`→`staging/`→`curated/`. **Déjà dans le rapport** (pourquoi `boto3` et pas DuckDB pour `raw/`, chapitre 4 §C19).

**C20 — Catalogue de données** : [`src/datacore/storage/lake/catalogue.py`](../../src/datacore/storage/lake/catalogue.py)
- `construire_catalogue()` / `catalogue_entree()` : génération par introspection réelle (`boto3` pour lister, `DESCRIBE` DuckDB pour le schéma), pas de catalogue maintenu à la main.

**C21 — Gouvernance des données** : [`src/datacore/storage/lake/`](../../src/datacore/storage/lake/)
- [`curated_bi.py`](../../src/datacore/storage/lake/curated_bi.py) — `pseudonyme()` (HMAC-SHA256) + `verifier_cle_configuree()` (garde-fou). **Déjà entièrement dans le rapport** — fonction la plus susceptible d'une question de sécurité/RGPD à l'oral, bien la maîtriser.
- [`purge.py`](../../src/datacore/storage/lake/purge.py) — procédure de purge RGPD, testée sur une partition synthétique réelle.

---

## Jalon transverse M4 — Restitution BI (Grafana)

**C16bis — Restitution OMEGA BI** : [`infra/grafana/dashboards/sla_omega_bi.json`](../../infra/grafana/dashboards/sla_omega_bi.json) (dashboard provisionné) + [`infra/grafana/provisioning/datasources/omega_bi.yaml`](../../infra/grafana/provisioning/datasources/omega_bi.yaml) (connexion `bi_reader` en lecture seule). Pas de code Python ici — à montrer dans Grafana directement (`http://localhost:3000`) plutôt que dans un éditeur, ou le JSON si la question porte sur le provisioning.

**C20bis — Monitorage du data lake** : [`src/datacore/storage/lake/monitoring.py`](../../src/datacore/storage/lake/monitoring.py)
- `enregistrer_catalogue()` / `enregistrer_purge()` / `verifier_sante_infrastructure()` : 3 relevés en ajout seul (append-only) vers le schéma `monitoring`.

Chaîne d'alerte : [`src/datacore/alerting/webhook.py`](../../src/datacore/alerting/webhook.py)
- `require_webhook_secret()` — authentification par secret partagé (`X-Webhook-Secret`), ajoutée après relecture de sécurité.
- `recevoir_alerte()` — reçoit l'alerte Grafana, relaie vers MailHog via `smtplib`.
- Testée de bout en bout par une vraie coupure MinIO, pas simulée. **Déjà dans le rapport.**

---

## Configuration

[`src/datacore/config.py`](../../src/datacore/config.py) — point d'entrée unique de toute la
configuration (une seule variable `os.environ.get("X", "défaut")` par
paramètre, jamais de valeur codée en dur ailleurs dans le code).
Repères utiles si la question porte sur un paramètre précis :
- Ligne 23 : `REPO_ROOT = Path(__file__).resolve().parents[2]` — base
  de tous les chemins relatifs (`data/raw/`, `data/interim/`).
- Lignes 30-43 : DSN de connexion aux deux bases Postgres (staging,
  entrepôt) — construits depuis les variables individuelles, jamais une
  chaîne de connexion codée en dur.
- Ligne 75 : `LAKE_PSEUDONYM_KEY` — **pas de valeur par défaut** (seul
  paramètre sans `os.environ.get(..., "défaut")`) : absence
  intentionnelle, c'est `verifier_cle_configuree()` (C21, déjà dans le
  rapport) qui refuse explicitement de continuer si elle est absente.
- Ligne 101 : `ALERTING_WEBHOOK_SECRET` — a bien un défaut pédagogique
  (`datacore-alerting-2026`), contrairement à la clé de pseudonymisation
  : à mentionner si la question porte sur la cohérence du traitement
  des secrets entre les deux.
- Appel à `load_dotenv()` en tête de fichier : nécessaire parce qu'un
  script Python lancé directement (hors Docker Compose) ne reçoit pas
  `.env` automatiquement, contrairement à un conteneur — point trouvé
  en relecture de `docs-scripts/` (voir [`synthese_technique_oral.md`](synthese_technique_oral.md)).

[`src/datacore/api/config.py`](../../src/datacore/api/config.py) — registre des rôles API (`Role` : 3
valeurs) et de `Principal` (identité résolue depuis une clé API) ;
modèle d'accès par groupe, à ne pas confondre avec `config.py` racine.

[`.env.example`](../../.env.example) — à montrer directement si la question porte sur
« comment les secrets sont-ils gérés » : chaque variable y est
commentée avec la compétence qui l'a introduite (ex.
`LAKE_PSEUDONYM_KEY` commenté « ne jamais réutiliser cette valeur
d'exemple »). `.env` réel jamais versionné ([`.gitignore`](../../.gitignore)) --
vérifiable en direct avec `git log --all --full-history -- .env`
(aucun résultat attendu).

## Infrastructure

[`infra/docker/docker-compose.yml`](../../infra/docker/docker-compose.yml) — les 8 services (voir chapitre 5
§6.1 du rapport pour le tableau port/URL). 3 Dockerfiles dédiés
([`api-mock.Dockerfile`](../../infra/docker/api-mock.Dockerfile), [`omega-data-api.Dockerfile`](../../infra/docker/omega-data-api.Dockerfile), [`alerting-webhook.Dockerfile`](../../infra/docker/alerting-webhook.Dockerfile)) — les autres
services utilisent une image officielle telle quelle (`postgres`,
`minio/minio`, `grafana/grafana-oss`, `mailhog/mailhog`), à mentionner
si la question porte sur « quels services avez-vous construits
vous-même vs. réutilisés tels quels ».

[`infra/grafana/`](../../infra/grafana/) — tout le provisioning Grafana est déclaratif (YAML/
JSON versionné), jamais configuré à la main dans l'interface :
- [`provisioning/datasources/omega_bi.yaml`](../../infra/grafana/provisioning/datasources/omega_bi.yaml) — connexion `bi_reader`.
- [`provisioning/dashboards/dashboards.yaml`](../../infra/grafana/provisioning/dashboards/dashboards.yaml) — déclare où Grafana va
  chercher les fichiers JSON de dashboards.
- [`dashboards/sla_omega_bi.json`](../../infra/grafana/dashboards/sla_omega_bi.json) / [`dashboards/monitoring_lake.json`](../../infra/grafana/dashboards/monitoring_lake.json) —
  les 2 dashboards eux-mêmes (C16bis/C20bis).
- [`provisioning/alerting/lake_monitoring.yaml`](../../infra/grafana/provisioning/alerting/lake_monitoring.yaml) — règle d'alerte +
  contact point webhook (secret inclus).

[`infra/minio/lake-reader-policy.json`](../../infra/minio/lake-reader-policy.json) — politique IAM MinIO restreignant
`lake_reader` au seul préfixe `curated_bi/` (C21, déjà dans le rapport
pour le principe, ce fichier JSON est la politique réelle appliquée si
la question demande à la voir).

---

## `api-mock` : simulateur des sources externes

Un seul fichier, [`api-mock/app.py`](../../api-mock/app.py), simule
**les trois sources externes** que le programme n'a jamais vraiment
contactées (FluxPro/TransFlow, le portail transporteur, les capteurs
IoT) -- à montrer directement si la question porte sur « comment vos
flux `temps réel`/`scraping` sont-ils générés » ou « interagissez-vous
avec de vrais systèmes externes » (réponse : non, voir
[`synthese_technique_oral.md` §3](synthese_technique_oral.md#3-anticipation-qa-jury--points-sensibles)
pour la réponse orale complète).

- `stream_capteurs()` (ligne ~210) — génère le flux SSE
  `/api/stream/capteurs` consommé par
  [`sse_consumer.py`](../../src/datacore/storage/lake/sse_consumer.py) (C19) : une boucle
  `while True` (processus réellement continu) qui tire une température
  (`random.gauss(3.0, 1.0)`), une géolocalisation (`random.uniform`)
  et un véhicule (`random.randint(1,15)`) aléatoires toutes les 2
  secondes -- aucun vrai capteur physique.
- `portail_index()` / `portail_colis()` (lignes ~252-270) — servent les
  pages HTML scrapées par
  [`scrape_colis_list()`/`scrape_colis_detail()`](../../src/datacore/ingestion/portail_scraping.py) (C8) : liste
  d'un échantillon aléatoire de colis (`random.sample(LIVRAISONS, ...)`)
  et fiche détail par `tracking_number`, générées depuis les fixtures
  JSON du mock, jamais un vrai site transporteur.
- `get_transporteurs()` / `get_tournees()` / `get_livraisons()`
  (lignes ~125-186) — routes REST consommées par
  [`transflow.py`](../../src/datacore/ingestion/transflow.py) (C8),
  même principe : données fixtures, pas un vrai TMS.
- `require_api_key()` (ligne ~65) — vérifie `X-API-Key: datacore-training-2026`
  sur toutes les routes sauf `/api/health` -- à mentionner si la
  question porte sur l'authentification côté source, symétrique à
  l'authentification côté API Omega Data (C12, `auth.py`).

---

## Questions transverses possibles (au-delà d'une compétence précise)

Questions qu'un jury pose souvent sur les choix d'architecture plutôt
que sur une compétence isolée. Chacune pointe vers un objet de
programmation précis, conformément au périmètre de ce document — les
questions de jugement sans objet technique (performance, passage à
l'échelle, "que feriez-vous différemment") sont traitées ailleurs
(voir note de périmètre en tête de document).

- **« Pourquoi Postgres et pas un autre SGBD ? »** — service `db` dans
  [`infra/docker/docker-compose.yml`](../../infra/docker/docker-compose.yml) (image `postgres`
  officielle) ; `STAGING_DB_DSN`/`OMEGA_BI_DB_DSN` dans
  [`src/datacore/config.py`](../../src/datacore/config.py) (lignes 30-43) construisent la
  chaîne de connexion depuis les variables d'environnement. Un seul
  moteur pour les deux bases (staging + entrepôt) plutôt que deux
  technologies différentes à maintenir.
- **« Que se passe-t-il si deux exécutions du pipeline ETL tournent en
  même temps ? »** — migration
  [`44a800999124_add_partial_unique_index_enforcing_one_.py`](../../src/datacore/storage/warehouse/migrations/versions/44a800999124_add_partial_unique_index_enforcing_one_.py)
  (index unique partiel `uq_dim_client_courant`) détecte le conflit en
  base ; le bloc `except psycopg2.errors.UniqueViolation` de
  `load_dim_client()` dans
  [`load_warehouse.py`](../../src/datacore/storage/warehouse/load_warehouse.py) le traduit en
  diagnostic explicite plutôt que de laisser une erreur SQL brute
  remonter.
- **« Qui peut lire les secrets (`.env`) ? »** — [`src/datacore/config.py`](../../src/datacore/config.py)
  lit uniquement l'environnement (`os.environ.get`), jamais une valeur
  codée en dur ; [`.gitignore`](../../.gitignore) exclut `.env`, vérifiable en
  direct par `git log --all --full-history -- .env` (aucun résultat) ;
  en conditions réelles, remplacé par un coffre-fort de secrets
  (commentaire explicite dans [`src/datacore/api/config.py`](../../src/datacore/api/config.py)).
- **« Pourquoi FastAPI pour l'API Omega Data ? »** — [`src/datacore/api/main.py`](../../src/datacore/api/main.py)
  (génération automatique de la spécification OpenAPI, exigée par le
  livrable C12, déjà dans le rapport) ; validation des types par
  Pydantic dans [`schemas.py`](../../src/datacore/api/schemas.py) plutôt que des vérifications
  manuelles.

---

## Conseil de préparation

Pour les fonctions déjà citées dans le rapport (`load_dim_client`,
`pseudonyme`, `deduplicate`, DuckDB/`httpfs`, `tracking_number`), le
texte du rapport donne déjà l'explication à voix haute prête à
l'emploi — relire ces 5 sections suffit. Pour le reste (C8, C9, C12
`db.py`/`auth.py`, C16, C19 `ingestion_batch`/`sse_consumer`, C20), ce
tableau donne seulement le point d'entrée : ouvrir le fichier et
relire la fonction citée avant l'oral, pas seulement cette ligne de
description.
