# Catalogue de données du data lake OMEGA LAKE

**Compétence couverte : C20 — Développer un catalogue de données**
**Épreuve associée : E7**

Périmètre de ce document, tel qu'explicitement élargi à la clôture de
C19 (voir
[`sequencement_bloc4.md` §4](sequencement_bloc4.md#4-point-de-vigilance-identifié-à-la-clôture-de-c19--périmètre-de-c20)) :
**construire** un contenu réel dans `staging/`/`curated/` (transformations
depuis `raw/`), **puis** le cataloguer — pas seulement documenter un
contenu déjà là.

---

## 1. Transformations `raw/` → `staging/` → `curated/`

`src/datacore/storage/lake/transform.py`. `staging/` et `curated/` sont
**régénérables** (contrairement à `raw/`, immuable) — chaque exécution
reconstruit entièrement `part-0.parquet` par flux depuis `raw/`, même
logique de rechargement complet que `load_warehouse.py` (C15).

| Étape | Traitement |
|---|---|
| `raw/` → `staging/` | Lecture de toutes les partitions `date=*` d'un flux (CSV/JSON/NDJSON selon le flux), déduplication basique (ligne strictement identique), écriture Parquet typé |
| `staging/` → `curated/` | Jointure aux dimensions conformées de l'entrepôt OMEGA BI, pour les flux où une clé naturelle réelle a été identifiée et vérifiée en C18 §5 |

**Jointures effectivement implémentées** — seulement celles conçues et
vérifiées en C18, pas une jointure de plus :

| Flux | Jointure curated | Clé |
|---|---|---|
| `capteurs_temperature` | `dimensions.dim_site` (entrepôt OMEGA BI) | `entrepot = dim_site.code` |
| `camera_comptage` | `dimensions.dim_site` | `entrepot = dim_site.code` |
| `rfid_scans` | `dimensions.dim_site` + `dimensions.dim_produit` | `entrepot = dim_site.code`, `produit_sku = dim_produit.sku` |
| `geoloc_flotte` | **Aucune** | — |
| `flux_sse_capteurs` | **Aucune** | — |

**Pourquoi `geoloc_flotte`/`flux_sse_capteurs` n'ont pas de jointure** :
la seule clé naturelle identifiée pour ces deux flux
(`vehicule_id` → `tournees.vehicule_id`) a été **explicitement exclue**
de toute automatisation en C18 §6 — elle permettrait de remonter
jusqu'à `tournees.chauffeur` (donnée personnelle), et le recouvrement
temporel entre les deux jeux de données est réel, pas seulement
théorique. `curated/` pour ces deux flux est donc une copie typée de
`staging/`, sans enrichissement relationnel — décision de conception,
pas un oubli.

### Vérifié en conditions réelles, pipeline complet

`raw/` alimenté pour de vrai (ingestion batch des 4 fichiers +
consommateur SSE quelques secondes), puis
`python3 -m datacore.storage.lake.transform` exécuté contre MinIO et
les deux bases Postgres réelles (staging, entrepôt OMEGA BI) :

| Flux | `raw/` | `staging/` | `curated/` | Écart |
|---|---|---|---|---|
| `capteurs_temperature` | 2592 | 2592 | 2592 | 0 |
| `geoloc_flotte` | 2160 | 2160 | 2160 | 0 |
| `camera_comptage` | 432 | 432 | 432 | 0 |
| `rfid_scans` | 3000 | 3000 | 3000 | 0 |
| `flux_sse_capteurs` | 6 | 6 | 6 | 0 |

Aucun écart de volumétrie entre zones : les jointures `curated/` sont
des `INNER JOIN` sur des clés vérifiées exhaustives (tout `entrepot`/
`produit_sku` présent dans les flux IoT a bien une correspondance dans
`dim_site`/`dim_produit`) — une perte de lignes aurait signalé une clé
mal formée ou une dimension incomplète, ni l'un ni l'autre ne s'est
produit.

---

## 2. Catalogue : introspection automatisée, pas documentation statique

`src/datacore/storage/lake/catalogue.py`. Le catalogue est **généré**
en interrogeant MinIO (`boto3` — présence, taille, date de dépôt) et
DuckDB (`DESCRIBE` — schéma réel du fichier) à chaque exécution, plutôt
que maintenu à la main dans un tableau — même principe que
`datacore.governance.audit_rgpd` (C16), qui interroge
`information_schema.columns` plutôt que de documenter une liste figée.
Un catalogue généré ne peut pas devenir silencieusement obsolète.

Chaque entrée porte exactement les 5 dimensions attendues par
l'issue #65 : **source**, **zone**, **format**, **schéma**,
**fraîcheur** (date de dernier dépôt) — plus le nombre de lignes.

### Extrait réel (`python3 -m datacore.storage.lake.catalogue`)

15 entrées (5 flux × 3 zones, toutes réellement présentes) :

```
raw      capteurs_temperature   csv       2592 lignes  [timestamp, entrepot, zone, temperature_c, alerte, date]
staging  capteurs_temperature   parquet   2592 lignes  [timestamp, entrepot, zone, temperature_c, alerte, date]
curated  capteurs_temperature   parquet   2592 lignes  [timestamp, entrepot, zone, temperature_c, alerte, date, entrepot_nom, entrepot_ville]
raw      geoloc_flotte          csv       2160 lignes  [timestamp, vehicule_id, lat, lon, vitesse_kmh, date]
staging  geoloc_flotte          parquet   2160 lignes  [timestamp, vehicule_id, lat, lon, vitesse_kmh, date]
curated  geoloc_flotte          parquet   2160 lignes  [timestamp, vehicule_id, lat, lon, vitesse_kmh, date]
raw      camera_comptage        csv        432 lignes  [timestamp, entrepot, zone, nb_passages, sens, date]
staging  camera_comptage        parquet    432 lignes  [timestamp, entrepot, zone, nb_passages, sens, date]
curated  camera_comptage        parquet    432 lignes  [timestamp, entrepot, zone, nb_passages, sens, date, entrepot_nom, entrepot_ville]
raw      rfid_scans             json      3000 lignes  [scan_id, timestamp, palette_id, entrepot, zone, produit_sku, date]
staging  rfid_scans             parquet   3000 lignes  [scan_id, timestamp, palette_id, entrepot, zone, produit_sku, date]
curated  rfid_scans             parquet   3000 lignes  [scan_id, timestamp, palette_id, entrepot, zone, produit_sku, date, entrepot_nom, produit_libelle, temperature_dirigee]
raw      flux_sse_capteurs      ndjson       6 lignes  [timestamp, entrepot, zone, temperature_c, vehicule_id, lat, lon, date]
staging  flux_sse_capteurs      parquet      6 lignes  [timestamp, entrepot, zone, temperature_c, vehicule_id, lat, lon, date]
curated  flux_sse_capteurs      parquet      6 lignes  [timestamp, entrepot, zone, temperature_c, vehicule_id, lat, lon, date]
```

On y lit directement, sans avoir besoin de relire le code : les
jointures `curated/` apparaissent dans le schéma
(`entrepot_nom`/`entrepot_ville` pour `capteurs_temperature`/
`camera_comptage` ; `entrepot_nom`/`produit_libelle`/
`temperature_dirigee` pour `rfid_scans`) ; `geoloc_flotte` et
`flux_sse_capteurs` n'en portent aucune, cohérent avec la décision RGPD
du §1 — le catalogue rend la décision de conception **visible**, pas
seulement documentée ailleurs.

**Colonne `date` inattendue** : présente sur les 15 entrées, pas définie
dans aucun fichier source. C'est le *hive partitioning* de DuckDB, qui
détecte automatiquement le segment `date=AAAA-MM-JJ` du chemin S3 et
l'expose comme colonne — comportement du moteur, pas une erreur.
Effet utile ici (trace la date d'ingestion du batch sans la coder en
dur), documenté pour ne pas être pris pour un bug plus tard.

---

## 3. Explorer le contenu directement

**Instantané au 23/09/2026** — 17 objets réellement présents dans le
bucket à cette date. Cette liste **n'est pas figée** : une nouvelle
exécution de l'ingestion batch crée une nouvelle partition `date=` sous
`raw/`, donc de nouveaux chemins. Pour la liste à jour, toujours
préférer `python3 -m datacore.storage.lake.catalogue` (§2) ou la
première cellule de
[`notebooks/exploration_omega_lake.ipynb`](../../notebooks/exploration_omega_lake.ipynb)
à cette copie figée.

```
raw/
  s3://omega-lake/raw/camera_comptage/date=2026-09-23/camera_comptage.csv
  s3://omega-lake/raw/capteurs_temperature/date=2026-09-23/capteurs_temperature.csv
  s3://omega-lake/raw/flux_sse_capteurs/date=2026-09-23/part-102732160283.ndjson
  s3://omega-lake/raw/flux_sse_capteurs/date=2026-09-23/part-102736163048.ndjson
  s3://omega-lake/raw/flux_sse_capteurs/date=2026-09-23/part-102738178957.ndjson
  s3://omega-lake/raw/geoloc_flotte/date=2026-09-23/geoloc_flotte.csv
  s3://omega-lake/raw/rfid_scans/date=2026-09-23/rfid_scans.json

staging/
  s3://omega-lake/staging/camera_comptage/part-0.parquet
  s3://omega-lake/staging/capteurs_temperature/part-0.parquet
  s3://omega-lake/staging/flux_sse_capteurs/part-0.parquet
  s3://omega-lake/staging/geoloc_flotte/part-0.parquet
  s3://omega-lake/staging/rfid_scans/part-0.parquet

curated/
  s3://omega-lake/curated/camera_comptage/part-0.parquet
  s3://omega-lake/curated/capteurs_temperature/part-0.parquet
  s3://omega-lake/curated/flux_sse_capteurs/part-0.parquet
  s3://omega-lake/curated/geoloc_flotte/part-0.parquet
  s3://omega-lake/curated/rfid_scans/part-0.parquet
```

**Lire un de ces fichiers depuis un terminal** (`.venv` actif, en une
commande, sans notebook) :

```bash
python3 -c "
from datacore.storage.lake.transform import connexion
con = connexion()
con.sql(\"SELECT * FROM 's3://omega-lake/curated/rfid_scans/part-0.parquet' LIMIT 20\").show()
"
```

`connexion()` (voir §1, `transform.py`) fait tout le travail de
configuration — extensions `httpfs`/`postgres` chargées, endpoint MinIO
et style d'adressage `path` déjà réglés, bases `staging`/`entrepot`
déjà attachées. Ne pas reconfigurer `httpfs` à la main à chaque fois :
c'est précisément pour éviter ça que cette fonction existe.

`notebooks/exploration_omega_lake.ipynb` fait la même chose pour les
4 formats réellement présents dans le lake (CSV, JSON liste, NDJSON,
Parquet), avec la sortie réellement exécutée plutôt qu'un exemple
recopié — utile pour voir d'un coup d'œil ce qui change entre `raw/`,
`staging/` et `curated/` pour un même flux.

---

## 4. Ce qui n'est pas fait

- Le catalogue est généré à la demande (`python3 -m ...catalogue`), pas
  exposé via une interface consultable — hors périmètre de C20 tel que
  formulé (documenter le contenu, pas construire un outil de catalogue
  dédié type DataHub/Amundsen, disproportionné pour ce volume).
- Pas de suivi d'évolution du schéma dans le temps (le catalogue reflète
  l'état courant, pas un historique des schémas passés) — pourrait
  devenir pertinent si le format d'un flux source changeait un jour,
  non nécessaire à ce stade.

---

## 5. Références

- [`architecture_omega_lake.md`](architecture_omega_lake.md) §5 — clés
  de jointure conçues en C18.
- [`architecture_omega_lake.md`](architecture_omega_lake.md) §6 —
  décision RGPD sur `vehicule_id`/`tournees.chauffeur`.
- [`sequencement_bloc4.md`](sequencement_bloc4.md) §4 — élargissement du
  périmètre de C20.
- [`integration_infrastructure_omega_lake.md`](integration_infrastructure_omega_lake.md) —
  mécanisme DuckDB↔MinIO↔Postgres (C19), réutilisé ici tel quel.
