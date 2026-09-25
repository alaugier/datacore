# Gestion opérationnelle de l'entrepôt OMEGA BI

**Compétence couverte : C16 — Assurer la gestion opérationnelle d'un environnement de données**
**Épreuve associée : E6**

Ce document décrit la gestion opérationnelle de l'entrepôt OMEGA BI :
sauvegardes planifiées, journalisation des opérations, tableau de bord
des indicateurs de service. Le registre RGPD de l'entrepôt fait l'objet
d'un document séparé :
[`registre_rgpd_entrepot.md`](registre_rgpd_entrepot.md).

Réalisé **après C17** (SCD2 sur `Dim_Client`), conformément à l'ordre
décidé dans [`sequencement_bloc3.md`](sequencement_bloc3.md) §2 : le
registre RGPD ne pouvait pas être conçu correctement avant que le schéma
historisé de `Dim_Client` existe.

---

## 1. Sauvegardes planifiées

`scripts/backup_omega_bi.sh --complet|--partiel`.

**Pourquoi deux modes, et pas un seul** : sur les 8 tables de l'entrepôt,
7 sont entièrement reconstructibles en rejouant le pipeline ETL (C15)
depuis la base de staging — une sauvegarde de ces tables n'apporte rien
qu'un rechargement ne referait pas. Seule `dimensions.dim_client` est
irremplaçable : historisée (SCD2, C17), son contenu ne peut pas être
régénéré depuis staging (qui ne connaît que l'état *courant* de chaque
client, jamais son historique de versions).

| Mode | Portée | Fréquence suggérée | Usage |
|---|---|---|---|
| `--partiel` | `dimensions.dim_client` uniquement | Quotidienne | Protège la seule donnée non reconstructible |
| `--complet` | Toute la base `datacore_omega_bi` | Hebdomadaire | Secours si le staging devient indisponible ou si la logique de l'ETL change |

**Planification** (exemple crontab, hors du Docker Compose local — à
adapter à un environnement de déploiement réel) :

```
0 2 * * *   cd /chemin/vers/datacore && ./scripts/backup_omega_bi.sh --partiel
0 3 * * 0   cd /chemin/vers/datacore && ./scripts/backup_omega_bi.sh --complet
```

Sauvegardes écrites dans `backups/` (non versionné, comme `data/raw/` —
voir `.gitignore`), horodatées. Chaque exécution (succès ou échec) est
journalisée dans `gouvernance.journal_operations` (§2) — un échec de
`pg_dump` déclenche un `trap` qui enregistre l'échec avant que le script
ne se termine, plutôt que de laisser l'incident invisible.

Vérifié pour de vrai : les deux modes exécutés contre l'entrepôt réel
(Docker Compose), fichiers produits (`--partiel` : 4 Ko ; `--complet` :
2 Mo) et journalisés avec succès.

---

## 2. Journalisation des opérations

Table `gouvernance.journal_operations` (créée en C16), alimentée par
[`datacore.governance.journal.journaliser`](../../src/datacore/governance/journal.py) —
un gestionnaire de contexte utilisé par `load_warehouse.py`,
`load_dim_temps.py` et `backup_omega_bi.sh` :

```python
with journaliser("load_warehouse") as contexte:
    ...
    contexte["details"] = "résumé de l'exécution"
```

Enregistre une ligne au début (`statut = en_cours`), puis la met à jour
à la sortie du bloc — `succes` avec le résumé fourni, ou `echec` avec le
message d'exception si le bloc lève une erreur (qui est ensuite
relancée : la journalisation observe, elle n'avale jamais une erreur
réelle). **Connexion dédiée, séparée de celle utilisée pour le
chargement** : si la transaction de chargement est annulée
(`ROLLBACK`), la ligne de journal décrivant cet échec doit malgré tout
être conservée — utiliser la même connexion l'aurait annulée avec le
reste.

Vérifié pour de vrai : succès et échec (simulé) journalisés
correctement, message d'erreur capturé, exception bien relancée.

Vue `gouvernance.v_dernieres_operations` : les 20 dernières exécutions,
avec durée calculée — support direct du tableau de bord (§3.4).

---

## 3. Tableau de bord des indicateurs de service

Trois vues SQL dans le schéma `exploitation` (accessibles en lecture
par le rôle `bi_reader`, C14 — héritage automatique via
`ALTER DEFAULT PRIVILEGES`, vérifié pour de vrai, aucune régénération de
droits nécessaire) :

### 3.1 `exploitation.v_taux_service_client`

Taux de service par client (`livre_a_lheure`), restreint aux expéditions
FluxPro/TransFlow (l'historique n'a pas de date de livraison prévue à
comparer, voir `modelisation_omega_bi.md` §5.1).

### 3.2 `exploitation.v_delai_moyen_transporteur`

Délai moyen de livraison par transporteur, toutes sources confondues —
le transporteur « Inconnu » regroupe les lignes issues de l'historique
(25 000 lignes sans transporteur identifié, attendu et documenté).

### 3.3 `exploitation.v_stock_disponible_site`

Quantité totale en stock et nombre de références par entrepôt.

### 3.4 Démonstration

[`notebooks/tableau_de_bord_sla_omega_bi.ipynb`](../../notebooks/tableau_de_bord_sla_omega_bi.ipynb) —
interroge les 3 vues et `gouvernance.v_dernieres_operations`, avec des
graphiques (matplotlib) en plus des tables texte déjà utilisées ailleurs
dans le projet — exécuté pour de vrai contre l'entrepôt, sorties et
figures capturées.

### 3.5 Outil de restitution de production : Grafana

**Décision prise le 24/09/2026**, après retour de formateur sur M2
(déjà clos) : vues SQL + notebook, bien que réels et vérifiés, ne
constituent pas une preuve de restitution suffisante pour C16 — un
outil de BI dédié est attendu.

**Le notebook n'est pas retiré ni réécrit** (voir §3.4 et `M2.md` §5,
mise à jour du 24/09/2026) : il reste la preuve exploratoire telle
qu'elle a été produite et validée au moment de la clôture de M2.
Grafana devient l'outil de restitution *de production*, en complément.

**Choix de Grafana parmi les options proposées** (Power BI, Databricks
SQL/Lakeview, Grafana) :
- Auto-hébergé, ajouté au `docker-compose.yml` existant du projet (au
  même titre que MinIO) — aucun compte ni service cloud externe requis,
  cohérent avec l'infrastructure 100 % locale du reste du programme.
- Se connecte directement en lecture aux 3 vues SQL du schéma
  `exploitation` (§3.1-3.3) via le rôle `bi_reader` déjà existant et
  déjà scopé (C14) — aucune vue ni droit supplémentaire à créer.
- Power BI écarté : usage réel passe par le Power BI Service (cloud
  Microsoft), hors du stack local du projet ; les fichiers `.pbix` ne
  se versionnent pas proprement dans git. Databricks SQL/Lakeview
  écarté : nécessite un workspace Databricks dédié, sans lien avec le
  reste de l'infra (Postgres + MinIO en local).

**Implémenté (issue #79, C16bis)** :
- Service `grafana` (`grafana/grafana-oss`) dans `docker-compose.yml`,
  auto-hébergé, volume dédié pour la persistance (`datacore-grafana-data`).
- Source de données provisionnée automatiquement
  (`infra/grafana/provisioning/datasources/omega_bi.yaml`) : Postgres,
  base `datacore_omega_bi`, utilisateur `bi_reader` — mot de passe lu
  depuis `BI_READER_PASSWORD` (`.env`), jamais codé en dur (même
  principe que `LAKE_PSEUDONYM_KEY`, voir `registre_rgpd_lake.md`).
- Dashboard provisionné automatiquement
  (`infra/grafana/dashboards/sla_omega_bi.json`) : les 3 indicateurs de
  §3.1-3.3 (taux de service par client, délai moyen par transporteur,
  stock disponible par site).

**Vérifié en conditions réelles** (24/09/2026) :
- Les 3 panels interrogés via l'API Grafana (`/api/ds/query`) renvoient
  des données réelles de l'entrepôt (ex. FreshMarket 90.6 % de taux de
  service, entrepôt de Lyon 11 190 unités en stock).
- Connexion confirmée avec les identifiants `bi_reader` réels (pas un
  compte admin) : `/api/datasources/uid/omega_bi_reader/health` renvoie
  `Database Connection OK`.
- Portée du rôle `bi_reader` reconfirmée côté Grafana : une lecture de
  `gouvernance.v_dernieres_operations` échoue en
  `permission denied for schema gouvernance` — cohérent avec le choix
  délibéré d'exclure `gouvernance` de `bi_reader` (§4, "préoccupation
  d'exploitation technique, pas un objet d'analyse métier"). Écriture
  non testée en direct (bloqué par la sandbox d'exécution), mais exclue
  par construction : seul `GRANT SELECT` est accordé à `bi_reader`
  (`sql/schema_entrepot_omega_bi.sql`), aucun `INSERT`/`UPDATE`/`DELETE`.
- **Faille d'infrastructure trouvée et corrigée en vérifiant** : les
  identifiants `.env` (`GRAFANA_ADMIN_PASSWORD` notamment) n'étaient pas
  réellement appliqués par `docker compose -f infra/docker/docker-compose.yml
  up -d` sans l'option `--env-file .env` — Docker Compose résout le
  fichier `.env` depuis le répertoire du fichier compose
  (`infra/docker/`), pas depuis le répertoire courant, donc silencieux
  retour aux valeurs par défaut codées dans `docker-compose.yml`.
  `README.md` et `api_omega_data.md` avaient déjà cette option ;
  `creation_entrepot_omega_bi.md` et `test_lake_pipeline.py` ne
  l'avaient pas — corrigés en conséquence. Sans ce correctif, le mot de
  passe admin Grafana serait resté silencieusement la valeur par défaut
  du fichier compose plutôt que celle, réelle, de `.env`.

**Bug réel trouvé le 25/09/2026, signalé par l'utilisateur** : les
panels affichaient "No data" dans le navigateur alors que mes propres
vérifications (`/api/ds/query` en HTTP direct) renvoyaient de vraies
données. Message d'erreur exact obtenu via le triangle d'avertissement
du panel et la console du navigateur : *"You do not currently have a
default database configured for this data source. Postgres requires a
default database with which to connect."* (levée par `SqlDatasource.ts`
côté React, pas par le backend).

**Cause réelle** : le provisioning ne renseignait le nom de la base
(`datacore_omega_bi`) qu'au niveau `database` (premier niveau du YAML),
pas dans `jsonData.database`. Le backend (santé de la source, `/api/ds/query`
appelé directement) se contente du premier niveau et fonctionne très
bien sans `jsonData.database` — mais l'éditeur de requête du navigateur
(React) vérifie `jsonData.database` *avant même d'envoyer la requête*
et refuse tout net si absent. **Mes vérifications de la veille (HTTP
direct, `curl`) ne passent jamais par ce chemin de code côté client et
ne pouvaient donc pas détecter ce bug** — angle mort méthodologique réel
de la vérification par API seule, distinct des limites déjà notées
("pas d'accès navigateur ici"). Corrigé : `jsonData.database:
$GF_OMEGA_BI_DB` ajouté dans
`infra/grafana/provisioning/datasources/omega_bi.yaml`, en plus du
champ de premier niveau (conservé, utilisé par le backend).

**Test de non-régression ajouté** (`test_grafana_omega_bi.py`) :
vérifie explicitement que `jsonData.database` est renseigné via l'API
`/api/datasources/uid/omega_bi_reader` — ce test aurait échoué avant le
correctif, contrairement aux tests déjà en place qui, eux, passaient
sans le détecter.

Accès : voir `README.md` §"Entrepôt OMEGA BI (C13-C17)".

---

## 4. Références

- [`pipelines_etl_omega_bi.md`](pipelines_etl_omega_bi.md) — pipeline
  ETL, désormais journalisé via ce livrable.
- [`historisation_dim_client_scd2.md`](historisation_dim_client_scd2.md) —
  raison d'être de la sauvegarde partielle (§1).
- [`registre_rgpd_entrepot.md`](registre_rgpd_entrepot.md) — registre
  RGPD de l'entrepôt (C16, second volet).
- [`sql/schema_entrepot_omega_bi.sql`](../../sql/schema_entrepot_omega_bi.sql) —
  schéma SQL brut complet, y compris `gouvernance.journal_operations`
  et les vues SLA décrites ici.
