# Index du code par compétence — préparation à l'oral

Objectif : pour chaque compétence, savoir en quelques secondes **quel
fichier ouvrir**, **quelle fonction montrer**, et **quoi dire
dessus** — pour répondre à « montrez-nous le bout de code qui fait
X ». Ce n'est pas un résumé à lire, c'est une carte de navigation :
s'entraîner à ouvrir chaque fichier cité et à relire la fonction
indiquée directement dans l'éditeur, pas seulement ce document.

Les compétences C1, C4-C7 n'ont pas de code associé (livrables
documentaires) — indiqué explicitement pour ne pas chercher un script
qui n'existe pas.

---

## Bloc 1 — Cadrage (documentaire, pas de code)

| C | Document à montrer |
|---|---|
| C1 | `docs/architecture/etude_faisabilite.md` (entretiens, RICE §6, SMART §7) |
| C2 | `docs/architecture/topographie_donnees.md` (glossaire §1, cartographie des sources §2) |
| C3 | `docs/architecture/architecture_cible.md` (AS IS/TO BE §1-2) |
| C4 | `docs/architecture/veille_technique_reglementaire.md` |
| C5 | `docs/architecture/feuille_de_route.md` (Gantt/PERT Mermaid §4) |
| C6 | `docs/architecture/supervision_projet.md` |
| C7 | `docs/architecture/communication_lancement.md` |

---

## Bloc 2 — Collecte & Stockage (C8-C12)

**C8 — Automatiser l'extraction** : `src/datacore/ingestion/`
- `run_extraction.py` — orchestrateur, appelle les 5 connecteurs dans l'ordre.
- `fluxpro.py` / `transflow.py` — requêtes SQL directes / appels API REST (`requests`).
- `portail_scraping.py` — `scrape_colis_list()`/`scrape_colis_detail()` : scraping HTML (pas d'API côté portail transporteur), à montrer si la question porte spécifiquement sur le scraping.
- `clients_files.py` — `read_norddrive()`/`read_freshmarket()`/`read_mediotex()` : un lecteur par format hétérogène.
- `landing.py` — écrit dans `data/interim/` (zone d'atterrissage, non versionnée).

**C9 — Requêtes SQL d'extraction** : `sql/extraction/01_commandes_par_client_periode.sql` → `05_evolution_delai_historique_par_annee.sql` (5 fichiers SQL bruts, pas de code Python ici) + `scripts/load_historique.sh`. Résultats réels documentés dans `docs/architecture/requetes_sql_extraction.md`.

**C10 — Agrégation/dédoublonnage** : `src/datacore/processing/`
- `clients_cleaning.py` — fonction `deduplicate()` : dédoublonnage au grain (commande, produit). **Déjà dans le rapport, chapitre 2 §C10.**
- `run_cleaning.py` — orchestrateur, écrit `data/interim/clients_consolidated.json`.

**C11 — Créer une base de données** : `src/datacore/storage/staging/`
- `models.py` — définitions SQLAlchemy Core des tables (`tracking_number` sans FK, clé métier). **Déjà dans le rapport.**
- `migrations/versions/` — historique Alembic (base de staging).
- `load_staging.py` — `main()` : transaction unique, voir chapitre 5 §6.5.1 du rapport.

**C12 — Partager le jeu de données** : `src/datacore/api/`
- `main.py` — routes FastAPI.
- `auth.py` — `get_current_principal()` + `_resolve_client_scope()` : un référent client qui demande un autre client est **silencieusement ramené** à son périmètre, pas juste rejeté. **Déjà dans le rapport (diagramme de séquence).**
- `db.py` — une connexion Postgres par requête (dépendance FastAPI), fermée en `finally` ; pas de pool — à mentionner si on demande pourquoi.
- `repository.py` / `schemas.py` — accès SQL / modèles Pydantic (→ spec OpenAPI auto-générée).

---

## Bloc 3 — Entrepôt OMEGA BI (C13-C17)

**C13 — Modéliser un entrepôt** : pas de code d'exécution (compétence de conception) — `docs/architecture/modelisation_omega_bi.md` (matrice de bus §2, MCD §4, le texte "pourquoi pas de `Fait_Livraison`" juste avant §5.2). Le schéma physique qui en découle est en C14.

**C14 — Créer un entrepôt** : `scripts/init_omega_bi_db.sh` (base + rôle `bi_reader`) + `alembic_omega_bi.ini` + `src/datacore/storage/warehouse/models.py` (3 schémas à la création) + `migrations/versions/` (5 fichiers notables : schéma initial, `ad009b506239` colonnes SCD2 C17, `44a800999124` index unique `uq_dim_client_courant`, `f6242611380a` schéma `gouvernance` C16, `a487cd05b8d5` schéma `monitoring` M4).

**C15 — Pipelines ETL** : `src/datacore/storage/warehouse/load_warehouse.py`
- `_run()` — orchestration complète : `truncate_warehouse()` puis chargement des 6 dimensions, puis des 3 faits, puis `commit()`. **Déjà dans le rapport (chapitre 5 §6.5.1, transaction unique).**
- `load_fait_expedition_historique()` — la logique de quarantaine (lignes non rapprochées mises de côté, pas rejetées silencieusement) : bon exemple si la question porte sur la qualité des données en sortie d'ETL.

**C16 — Gestion opérationnelle** : `src/datacore/governance/`
- `journal.py` — `journaliser()` : context manager, connexion Postgres séparée du chargement, commit immédiat du statut `en_cours`. **Déjà dans le rapport (pourquoi une connexion séparée).**
- `audit_rgpd.py` — `auditer()` : scanne les noms de colonnes de l'entrepôt à la recherche de motifs de données personnelles (`colonnes_suspectes()`), audit automatisé plutôt que déclaratif.
- `scripts/backup_omega_bi.sh` — sauvegarde partielle/complète planifiée.

**C17 — SCD2** : `src/datacore/storage/warehouse/load_warehouse.py`, fonction `load_dim_client()`. **Déjà entièrement dans le rapport** (listing + explication de `r`/`current`/`mapping`, chapitre 3 §C17) — relire ce listing avant l'oral, c'est probablement la fonction la plus technique à défendre.

---

## Bloc 4 — Data Lake OMEGA LAKE (C18-C21)

**C18 — Architecture du data lake** : `docs/architecture/architecture_omega_lake.md` (schema-on-read §1) + `docs/architecture/organisation_omega_lake.md` (hiérarchie bucket→zone→flux→objet) + `src/datacore/storage/lake/transform.py` pour la jointure DuckDB/`httpfs` réelle (configuration déjà dans le rapport, chapitre 4).

**C19 — Intégration infrastructure** : `src/datacore/storage/lake/`
- `ingestion_batch.py` — `ingerer_flux_batch()` : dépôt `boto3` des 4 flux IoT batch dans `raw/`, copie fidèle octet pour octet.
- `sse_consumer.py` — consommateur du flux temps réel, fenêtré par intervalle de 5 minutes ; testé par coupure brutale réelle (`kill -9`). Processus continu, pas un script à exécution unique — à préciser si on vous demande de le lancer en direct.
- `transform.py` — jointure DuckDB `raw/`→`staging/`→`curated/`. **Déjà dans le rapport** (pourquoi `boto3` et pas DuckDB pour `raw/`, chapitre 4 §C19).

**C20 — Catalogue de données** : `src/datacore/storage/lake/catalogue.py`
- `construire_catalogue()` / `catalogue_entree()` : génération par introspection réelle (`boto3` pour lister, `DESCRIBE` DuckDB pour le schéma), pas de catalogue maintenu à la main.

**C21 — Gouvernance des données** : `src/datacore/storage/lake/`
- `curated_bi.py` — `pseudonyme()` (HMAC-SHA256) + `verifier_cle_configuree()` (garde-fou). **Déjà entièrement dans le rapport** — fonction la plus susceptible d'une question de sécurité/RGPD à l'oral, bien la maîtriser.
- `purge.py` — procédure de purge RGPD, testée sur une partition synthétique réelle.

---

## Jalon transverse M4 — Restitution BI (Grafana)

**C16bis — Restitution OMEGA BI** : `infra/grafana/dashboards/sla_omega_bi.json` (dashboard provisionné) + `infra/grafana/provisioning/datasources/omega_bi.yaml` (connexion `bi_reader` en lecture seule). Pas de code Python ici — à montrer dans Grafana directement (`http://localhost:3000`) plutôt que dans un éditeur, ou le JSON si la question porte sur le provisioning.

**C20bis — Monitorage du data lake** : `src/datacore/storage/lake/monitoring.py`
- `enregistrer_catalogue()` / `enregistrer_purge()` / `verifier_sante_infrastructure()` : 3 relevés en ajout seul (append-only) vers le schéma `monitoring`.

Chaîne d'alerte : `src/datacore/alerting/webhook.py`
- `require_webhook_secret()` — authentification par secret partagé (`X-Webhook-Secret`), ajoutée après relecture de sécurité.
- `recevoir_alerte()` — reçoit l'alerte Grafana, relaie vers MailHog via `smtplib`.
- Testée de bout en bout par une vraie coupure MinIO, pas simulée. **Déjà dans le rapport.**

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
