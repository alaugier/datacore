# Synthèse technique pour préparation à l'oral

## 0. Origine de ce document

Pour préserver le budget de tokens, chaque script du projet a été
documenté via GitHub Copilot Chat (hors dépôt, dossier
`docs-scripts/`) : une base de compréhension la plus fiable possible,
sans objectif de versionnement rigoureux des descriptions au fil des
évolutions du code -- Copilot a fidèlement décrit ce qui lui a été
fourni à chaque fois. Ce document en est la relecture critique :
vérifié fichier par fichier contre le code réel du dépôt, avec deux
objectifs -- préparer les questions techniques possibles à l'oral, et
détecter d'éventuels bugs silencieux ou manques. Aucun bug réel n'a
été trouvé dans le code du dépôt lors de cette relecture ; les écarts
relevés viennent uniquement du fait que certaines descriptions n'ont
pas été regénérées après une évolution ultérieure du code qu'elles
documentaient (détaillé en §1) -- utile à savoir avant de citer un
chiffre ou un comportement depuis `docs-scripts/` à l'oral.

---

## 1. Verdict sur la documentation Copilot (`docs-scripts/`)

### 1.1 Règle générale : `_v2`/`_v3` prime sur le fichier sans suffixe

Partout où une paire `desc_X.py.md` / `desc_X_v2.py.md` (ou `_v3`)
existe, la version suffixée est systématiquement la plus récente et
correspond au code réel ; la version sans suffixe est obsolète.
Confirmé sur 7 paires dans `src/` (dates de modification + diff de
contenu) et sur plusieurs fichiers de `tests/`. **Ne jamais citer un
chiffre (nombre de tests, comportement décrit) depuis un fichier sans
suffixe `_v2` si une version `_v2` existe.**

### 1.2 Problèmes concrets trouvés

| Fichier Copilot | Problème | Réalité |
|---|---|---|
| `ingestion/desc_..._config_v1.py.md` | Documente `src/datacore/ingestion/config.py`, qui **n'existe plus** | Déplacé à la racine (`src/datacore/config.py`) ; le fichier réel a aussi gagné `load_dotenv()` et une profondeur `REPO_ROOT` différente — changement de comportement, pas qu'un déplacement |
| 3 migrations Alembic de l'entrepôt | Non documentées | `ad009b506239` (colonnes SCD2, C17), `44a800999124` (index unique `uq_dim_client_courant`), `f6242611380a` (schéma `gouvernance`) — toutes trois citées dans le rapport, aucune dans docs-scripts |
| `.github/workflow/desc_...ci.yml.md` | Décrit un pipeline à 2 jobs (`lint`→`test`), **aucune mention de `mypy`** | 3 jobs réels (`lint`, `typecheck`, `test`), `test` dépend des deux premiers — ce doc contredit directement le rapport (correct, lui) |
| `infra/docker/desc_...docker-compose.yml.md` (sans `_v2`) | S'arrête à `grafana`, **manque `mailhog` et `alerting-webhook`** (ajouts M4) ; 1652 lignes avec du remplissage générique répété | Le `_v2` correspond exactement aux 8 services réels |
| `infra/grafana/.../desc_..._lake_monitoring.yaml.md` (sans `_v2`) | Zéro mention du secret webhook (`X-Webhook-Secret`) | Le `_v2` documente l'authentification ajoutée après la relecture de sécurité M4 |
| `scripts/desc_..._export_mermaid_diagrams.py.md` | Documente l'ancien flag `-w 1600` de mermaid-cli | Corrigé cette session (`--size`, nouvelle version de `mermaid-cli`) |
| `tests/.../desc_..._test_alerting_webhook.py.md` | 5 tests documentés | 10 réels — manquent entièrement les tests d'auth (401), de payload malformé (400) et d'échec SMTP (502), soit exactement le correctif de robustesse déjà narré au chapitre M4 |
| `tests/.../desc_..._test_curated_bi.py.md` | Manque 8 des 15 tests réels | Toute la suite de `verifier_cle_configuree()` (clé absente/vide/trop courte/placeholder/ancien repli codé en dur) absente — c'est pourtant le cœur du récit C21 du rapport |
| `tests/.../desc_..._test_load_warehouse.py.md` | Manque les 4 tests SCD2 | Détection de changement, première insertion, réutilisation sans changement, diagnostic de violation d'index -- la story C17 du rapport, non testée dans ce doc |
| `tests/.../desc_..._test_load_dim_temps.py.md` (v1) | Affirme explicitement que la plage inversée et le rowcount ne sont *pas* testés | Faux pour le code actuel — ces tests existent (le `_v2` les documente correctement) |
| `tests/.../desc_..._test_monitoring.py.md` (v1) | 4 tests | 6 réels (`_v2` correct) |
| `tests/.../desc_..._test_grafana_lake_monitoring.py.md` (v1) | 6 tests | 7 réels (`_v2` correct) |

### 1.3 Fichiers à écarter purement et simplement

- **`desc_pyproject_toml_v1.md`** : snapshot partiel (manque `[build-system]`/`[project]`/`[tool.setuptools]`). À ignorer.
- **`desc_pyproject_toml_v2.md`** et **`pyproject_v2.toml.md`** : identiques entre eux et au `pyproject.toml` réel — redondants, n'en garder qu'un.
- **`en_attente_analyse.txt`** : pas de la documentation — un journal brut de vérifications ponctuelles (comptage de valeurs nulles), qui se termine sur une vraie `SyntaxError` Python. À écarter.
- **`desc_alembic.ini.md`** : contenu final correct (les deux environnements Alembic, staging vs entrepôt) mais le fichier inclut une auto-correction de Copilot en cours de texte ("Tu as raison : ma remarque précédente était incomplète…") -- à nettoyer si réutilisé tel quel, le lire en entier plutôt que s'arrêter à la première moitié.

### 1.4 Fichiers vérifiés corrects, aucune action nécessaire

`desc_tests_unit_test_api_repository.py.md`, `scripts/init_omega_bi_db.sh` et `load_historique.sh` (docs associées), les 4 docs de notebooks, la doc api-mock (`X-API-Key: datacore-training-2026` correct).

---

## 2. Points techniques pour l'oral (non déjà couverts dans le rapport)

### Configuration
- `datacore/config.py` appelle explicitement `load_dotenv()` : les scripts Python lancés directement (hors Docker Compose) ne reçoivent pas `.env` automatiquement, contrairement aux conteneurs -- un point concret si la question "comment les secrets arrivent-ils jusqu'au script ?" se pose.

### API Omega Data (C12)
- `api/db.py` ouvre une connexion Postgres **par requête** (dépendance FastAPI, fermée dans un `finally` même en cas d'exception), pas de pool de connexions -- choix de simplicité assumé à cette échelle, à mentionner si la question "pourquoi pas de pool de connexions ?" se pose.
- `tests/integration/test_api_routes.py` teste l'autorisation/le scoping par rôle via le mécanisme `app.dependency_overrides` de FastAPI (pas de vraies clés API) -- isole le test de la logique d'autorisation de celui de la couche repository, testée séparément.

### Méthodologie de test
- Convention uniforme sur tous les tests unitaires : connexion/curseur Postgres **simulés** (`FakeConnection`/`FakeCursor`, même motif réutilisé dans `load_dim_temps`, `load_warehouse`, `load_staging`, `monitoring`), délibérément pour que les tests unitaires restent rapides et ne nécessitent aucun service Postgres dans la CI (confirmé : `ci.yml` ne provisionne aucun service `db`). La vérification contre une vraie base est reportée aux tests d'intégration et aux exécutions manuelles via Docker Compose (déjà décrites au chapitre C14/§6.5 du rapport). Réponse directe si la question "vos tests touchent-ils vraiment PostgreSQL ?" se pose.
- Les fakes sont **paramétrables** (ex. `rowcount_insere=1` pour simuler un `ON CONFLICT` qui rejette silencieusement une ligne) -- permet de prouver qu'une fonction renvoie bien ce qui a été **réellement inséré**, pas ce qui a été envoyé, sans base réelle. Bonne réponse concrète si la question "comment testez-vous l'idempotence sans base réelle ?" se pose.
- **SCD2 (C17)** : 4 tests dédiés (première insertion, réutilisation sans changement, changement détecté → nouvelle version, diagnostic de violation d'index unique) -- chiffre à citer si la question "comment C17 est-il testé ?" se pose au-delà du seul extrait déjà dans le rapport.
- **Garde-fou de pseudonymisation (C21)** : 8 tests négatifs dédiés, un par chemin de rejet (clé absente, vide, trop courte, valeur d'exemple connue, ancien repli codé en dur) plus un test du scénario de fuite par ré-identification et un test de synchronisation `.env`/`.env.example` -- chiffre à citer si la question "avez-vous vraiment testé ce garde-fou, ou juste le cas nominal ?" se pose.
- La CI exécute `pytest tests/unit tests/integration` (176 tests au 21/10/2026) seulement si `ruff` **et** `mypy` passent tous les deux -- graphe de dépendance à savoir dessiner/expliquer à l'oral.

---

## 3. Anticipation Q&A jury — points sensibles

Issue #96 (milestone M6). Format : question probable, réponse
synthétique prête à dire à voix haute (pas à lire), renvoi au livrable
preuve. Les questions purement techniques pointant vers un objet de
code précis sont dans
[`index_code_par_competence.md`](index_code_par_competence.md) -- ici,
des choix d'architecture ou des écarts qui demandent une réponse
argumentée plutôt qu'un extrait de code.

**« Pourquoi SCD2 sur `Dim_Client` et pas SCD1 (écraser l'ancienne
valeur) ? »**
Parce que les faits déjà chargés (`Fait_Expedition`, `Fait_Commande`)
référencent la `client_key` qui était courante au moment de leur
chargement -- en SCD1, un changement de secteur client réécrirait
silencieusement l'historique analytique (une commande passée l'an
dernier semblerait avoir été passée par le nouveau secteur). SCD2 crée
une nouvelle ligne/nouvelle clé plutôt que d'écraser, donc les faits
historiques restent exacts pour la période où ils ont eu lieu. Testé
par 4 tests dédiés (chapitre 3 §C17 du rapport,
[`index_code_par_competence.md`](index_code_par_competence.md) pour le
fichier exact).

**« Pourquoi HMAC pour pseudonymiser `vehicule_id`, pas un hash
simple ou un chiffrement réversible ? »**
Un hash simple (sans clé) aurait été recalculable par force brute --
seulement 15 véhicules dans le jeu de données, un attaquant essaierait
les 15 identifiants connus en quelques secondes. HMAC à clé secrète
rend ce recalcul impossible sans la clé. Chiffrement réversible
écarté à dessein : le but n'est pas de pouvoir retrouver
`vehicule_id` depuis `curated_bi/`, c'est d'empêcher `lake_reader` de
le faire -- un pseudonyme stable (même entrée → même sortie, toujours)
suffit pour les besoins d'analyse BI (regrouper par véhicule) sans
jamais avoir besoin de revenir en arrière. Garde-fou testé par 8 tests
négatifs dédiés (chapitre 4 §C21 du rapport).

**« Pourquoi Grafana plutôt que Power BI ou Databricks pour la
restitution BI ? »**
Power BI écarté : l'usage réel passe par le Power BI Service (cloud
Microsoft), hors du stack 100 % local du programme, et les fichiers
`.pbix` ne se versionnent pas proprement dans Git. Databricks
SQL/Lakeview écarté : nécessite un workspace Databricks dédié, sans
lien avec le reste de l'infrastructure (Postgres + MinIO en local).
Grafana est auto-hébergé, open source, ajouté au `docker-compose.yml`
existant sans nouveau compte ni service cloud -- cohérent avec la
stratégie de sobriété retenue dès C3
([`gestion_operationnelle_omega_bi.md` §3.5](gestion_operationnelle_omega_bi.md#35-outil-de-restitution-de-production--grafana),
chapitre 5 du rapport).

**« Pourquoi pas d'orchestrateur (Airflow, Dagster) pour les
pipelines ? »**
Question posée explicitement au formateur plutôt que tranchée seul :
pas exigé pour valider la compétence, mais constitue un plus. Trois
raisons au choix de ne pas en intégrer un : le référentiel (C8/C15/
C19) n'exige aucun outil d'orchestration précis ; le coût est concret,
pas hypothétique (un orchestrateur ajoute au minimum trois services --
initialisation, ordonnanceur, interface web -- plus sa propre base de
métadonnées, sur une infrastructure qui en compte déjà huit) ; et
surtout aucun pipeline du programme ne s'exécute aujourd'hui selon une
cadence récurrente réelle à orchestrer -- chacun est invoqué à la
demande sur un jeu de données statique (chapitre 5 du rapport,
« Pourquoi pas un orchestrateur »).

**« Quels écarts avez-vous eus par rapport au cahier des charges ? »**
Six écarts réels sur l'ensemble du programme, tous décidés avant
codage ou documentés au moment où ils ont été trouvés, jamais
découverts a posteriori en relisant le cahier des charges après coup :
- **C17** (M2) : attributs historisés (`nom`/`secteur`) différents de
  ceux prévus dans l'issue initiale (`adresse`/`contrat`, absents du
  jeu de données pédagogique) -- décidé avec l'utilisateur avant
  codage.
- **C20** (M3) : périmètre élargi pour construire le contenu réel de
  `staging/`/`curated/`, pas seulement cataloguer `raw/` comme le
  texte initial de l'issue le suggérait.
- **C21/RGPD** (M3) : la pseudonymisation, d'abord écartée sur une
  analyse incomplète, a été réintroduite après relecture externe.
- **M4** (jalon transverse) : pas prévu dans la planification
  initiale -- ajouté après un retour de formateur établissant que les
  vues SQL + notebook ne suffisaient pas comme preuve de restitution,
  confirmé depuis par la lecture littérale du référentiel (C16
  activité 6 exige un « tableau de bord »).
- **Bibliographie** (M5) : ajoutée hors séquencement initial, à la
  demande de l'utilisateur.
- **Découpage en PR de M5** : 3 issues séquencées, livrées en pratique
  sur une seule PR -- `dev` ne portait pas encore l'infrastructure
  LaTeX tant que la première n'était pas mergée.

Aucun écart n'a modifié le périmètre fonctionnel livré ; tous les
écarts touchent soit des détails d'attributs/d'implémentation, soit
l'organisation du travail, jamais une compétence manquante ou un
livrable non conforme (détail complet dans chaque
`docs/comptes_rendus/MN.md` §4).

---

## 4. Ce qui n'a pas été retenu

Tout ce qui, dans `docs-scripts/`, décrit correctement et sans ajout
utile un comportement déjà couvert par le rapport LaTeX (clé
`tracking_number`, SCD2, pseudonymisation HMAC, séparation DuckDB/
`boto3`, absence de `Fait_Livraison`, transactions/rollback) n'est pas
repris ici -- redondant avec les chapitres 2 à 6 du rapport.
