# Aide-mémoire — Shell, Docker Compose, Grafana (provisioning)

Voir `README.md` de ce dossier pour l'esprit de ces fiches (piège réel
rencontré, pas la doc générale de l'outil).

### `docker compose -f <chemin> ...` et `.env`

Sans `--env-file .env`, Docker Compose résout le fichier `.env` depuis
le répertoire du fichier passé à `-f` (ici `infra/docker/`), **pas**
depuis le répertoire courant — donc silencieux retour aux valeurs par
défaut codées en dur dans `docker-compose.yml` (`${VAR:-defaut}`),
même en lançant la commande depuis la racine du dépôt où se trouve le
vrai `.env`. Piège trouvé le 25/09/2026 : `GRAFANA_ADMIN_PASSWORD` de
`.env` était ignoré, le mot de passe réellement actif restait la
valeur par défaut du fichier compose.

Utilisé dans : `README.md`, `docs/architecture/creation_entrepot_omega_bi.md`,
`tests/integration/test_lake_pipeline.py`, `tests/integration/test_grafana_omega_bi.py`.

```bash
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d
```

### Provisioning Grafana — source de données Postgres : `jsonData.database`

Le champ `database` de premier niveau (dans le YAML de provisioning)
suffit pour le backend (health check de la source, appel direct à
`/api/ds/query`) — mais **pas** pour l'éditeur de requête du navigateur
(React), qui vérifie `jsonData.database` avant même d'envoyer la
requête et refuse net si absent (`"You do not currently have a default
database configured for this data source."`). Ce chemin de code côté
client n'est jamais exercé par un appel HTTP direct (`curl`), donc
invisible en testant uniquement l'API. Piège trouvé le 25/09/2026,
signalé par un utilisateur testant depuis un vrai navigateur.

Utilisé dans : `infra/grafana/provisioning/datasources/omega_bi.yaml`.

```yaml
jsonData:
  database: $GF_OMEGA_BI_DB   # en plus du champ `database` de premier niveau
```

### Provisioning Grafana — panels en SQL brut : `editorMode` / `rawQuery`

Un panel provisionné avec seulement `rawSql` (sans `editorMode: "code"`
ni `rawQuery: true`) reste en mode "builder" (vide) à l'ouverture dans
l'éditeur — bonne pratique systématique pour tout dashboard écrit à la
main plutôt que construit via l'éditeur visuel de Grafana.

Utilisé dans : `infra/grafana/dashboards/sla_omega_bi.json`.

```json
{ "rawSql": "SELECT ...", "format": "table", "editorMode": "code", "rawQuery": true }
```

### Panel `bargauge` avec plusieurs lignes de résultat : `reduceOptions.values`

Sans `"values": true`, un panel `bargauge` **réduit silencieusement**
toutes les lignes du résultat à une seule valeur agrégée (calc par
défaut, ex. `lastNotNull` — donc la dernière ligne du tri, pas une
erreur visible) au lieu d'afficher une barre par ligne. Piège trouvé le
25/09/2026 : 3 clients dans la requête, 1 seul visible à l'écran.

Utilisé dans : `infra/grafana/dashboards/sla_omega_bi.json`.

```json
"reduceOptions": { "calcs": ["lastNotNull"], "values": true, "fields": "" }
```

### Provisioning Grafana — alerting déclaratif (`contactPoints`/`policies`/`groups`)

Un point de contact et une règle d'alerte se provisionnent comme les
datasources/dashboards, dans `infra/grafana/provisioning/alerting/`
(clé `apiVersion: 1`, puis `contactPoints`/`policies`/`groups`). Une
règle a besoin d'au moins une requête (`data[].model`, avec
`editorMode`/`rawQuery` comme pour un panel) et d'une expression de
seuil (`datasourceUid: "__expr__"`, `type: threshold`) référencée par
`condition`.

**Délai réel entre "alerte active" et "e-mail reçu"** : Grafana
regroupe les notifications (`group_wait`, ~30 s par défaut avant le
premier envoi d'un nouveau groupe) — l'alerte peut passer à l'état
`active` côté `/api/alertmanager/.../alerts` plusieurs secondes avant
que le point de contact soit réellement notifié. Vérifié le 25/09/2026 :
~20 s d'écart, pas un échec de livraison.

Utilisé dans : `infra/grafana/provisioning/alerting/lake_monitoring.yaml`.
