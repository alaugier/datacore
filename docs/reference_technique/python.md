# Python — bibliothèques utilisées dans ce projet

Voir [`README.md`](README.md) pour le principe de ce fichier (ancré
dans l'usage réel, pas une doc d'API générale). Ajouté au fil de
l'introduction de chaque bibliothèque, pas rétroactivement pour tout
le projet.

---

## boto3 (introduit en C19)

Client officiel AWS pour Python — utilisé ici contre **MinIO**, pas
AWS (compatible S3, pas identique).

### `boto3.client("s3", **kwargs)`
Fonction top-level (`from boto3 import client` fonctionne) — mais elle
ne fait qu'**instancier** un client. Les méthodes d'action
(`upload_file`, `get_object`, `head_object`, ...) sont sur l'**objet
retourné**, jamais importables individuellement (pas de
`from boto3 import upload_file`, ça n'existe pas).

boto3 propose deux styles d'API distincts : **client** (bas niveau,
proche de l'appel REST — `put_object`/`get_object`, kwargs nommés) et
**resource** (orienté objet — `s3.Bucket(nom).objects...`). Ce projet
n'utilise que le style **client**.

Contre MinIO (pas AWS S3), deux kwargs sont indispensables — sans eux,
boto3 vise l'endpoint AWS par défaut et échoue :
- `endpoint_url` : l'adresse de l'instance MinIO.
- `config=Config(s3={"addressing_style": "path"})` : MinIO exige
  l'adressage `path` (`http://endpoint/bucket/clé`), pas le style
  `virtual-hosted` par défaut de boto3/AWS
  (`http://bucket.endpoint/clé`).

Utilisé dans : `src/datacore/storage/lake/ingestion_batch.py::client()`

```python
boto3.client(
    "s3",
    endpoint_url=f"http://{OMEGA_LAKE_S3_ENDPOINT}",
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD,
    config=Config(s3={"addressing_style": "path"}),
)
```

### `s3.upload_file(Filename, Bucket, Key)`
Méthode d'instance. **Arguments positionnels dans cet ordre précis**
(chemin local, bucket, clé) — à ne pas confondre avec `put_object`, qui
prend des kwargs nommés (`Bucket=`, `Key=`, `Body=`) et un contenu déjà
en mémoire plutôt qu'un chemin de fichier. Gère automatiquement le
multipart pour les gros fichiers (transparent ici, aucun des fichiers
IoT n'en a besoin).

Utilisé dans : `ingestion_batch.py::ingerer_flux_batch()`

### `s3.get_object(Bucket, Key)` / `s3.head_object(Bucket, Key)`
`get_object` renvoie un dict dont `["Body"]` est un flux à lire
(`.read()` renvoie les octets bruts, une seule fois — pas rembobinable).
`head_object` renvoie les métadonnées seules (taille, type), sans
transférer le contenu — utile pour confirmer qu'un objet existe sans le
télécharger.

Utilisé dans : vérification de fidélité SHA-256
(`notebooks/verification_duckdb_minio_omega_lake.ipynb`).

### `s3.delete_object(Bucket, Key)`
Suppression d'un objet. Pas de suppression par motif/préfixe en un seul
appel — pour vider un préfixe entier, il faut lister (`list_objects_v2`)
puis supprimer chaque clé.

### `s3.list_objects_v2(Bucket, Prefix=..., MaxKeys=...)`
Liste les objets d'un bucket, filtrés par préfixe (`Prefix` — pas de
wildcard, juste un préfixe de chemin littéral, ex. `"curated/rfid_scans/"`).
Deux pièges :
- `["KeyCount"]` (nombre d'objets) est **toujours présent**, mais
  `["Contents"]` (la liste elle-même) est **absent**, pas une liste
  vide, quand il n'y a aucun objet — d'où
  `reponse.get("Contents", [])` plutôt que `reponse["Contents"]`, et
  `reponse.get("KeyCount", 0)` par prudence symétrique.
- `MaxKeys=1` est le moyen efficace de répondre « est-ce que ce
  préfixe contient quelque chose ? » sans lister tout le contenu —
  utilisé pour ça dans `catalogue.py::_entree_existe`, avant de lancer
  une introspection DuckDB coûteuse pour rien sur un flux/zone vide.

Chaque élément de `["Contents"]` porte `["LastModified"]` (un
`datetime` timezone-aware, pas une chaîne) — c'est la source de la
« fraîcheur » dans le catalogue (`catalogue.py`), pas une donnée du
fichier lui-même.

Utilisé dans : `catalogue.py::catalogue_entree()`.

---

## DuckDB (introduit en C19)

Moteur SQL analytique embarqué (aucun serveur à opérer) — lit le
Parquet/CSV/JSON nativement et peut se connecter à Postgres via une
extension.

### `duckdb.connect()`
Session **en mémoire** par défaut (rien de persistant) — passer un
chemin de fichier (`duckdb.connect("fichier.db")`) pour une base
persistante, non utilisé dans ce projet (chaque script/notebook ouvre
une session éphémère).

### `INSTALL <extension>; LOAD <extension>;`
Les extensions (`httpfs` pour S3/HTTP, `postgres` pour se connecter à
Postgres) ne sont **pas incluses par défaut** — à charger explicitement,
à chaque nouvelle connexion (`INSTALL` télécharge, une fois pour
toutes sur la machine ; `LOAD` active pour la session en cours, à
refaire à chaque `connect()`).

### `con.sql(requete)`
Exécute du SQL, renvoie une relation (pas immédiatement les données).
`.show()` affiche un aperçu formaté (utile en notebook/REPL) ;
`.fetchall()` matérialise en liste de tuples Python ; `.df()` matérialise
en DataFrame pandas (non utilisé dans ce projet — voir la note ci-dessous).

### `SET s3_endpoint=...; SET s3_url_style='path'; ...`
Configuration de l'extension `httpfs` pour un stockage S3-compatible
**non-AWS** (MinIO). Sans `s3_url_style='path'`, DuckDB utilise le
style d'adressage AWS par défaut, que MinIO refuse — piège spécifique
à MinIO, pas nécessaire contre un vrai bucket AWS S3.

### `ATTACH '<chaîne_connexion>' AS <alias> (TYPE postgres, READ_ONLY)`
Attache une base Postgres externe, interrogeable ensuite comme un
schéma (`<alias>.<schéma_pg>.<table>`). `READ_ONLY` empêche toute
écriture accidentelle depuis DuckDB — utilisé systématiquement dans ce
projet (DuckDB ne doit jamais modifier la base de staging/l'entrepôt).

### `read_csv_auto(chemin)` / `read_json_auto(chemin)` / `read_parquet(chemin)`
Fonctions **table** : s'utilisent directement dans une clause `FROM`,
pas en préambule séparé (`FROM read_parquet('s3://...')`, pas
`df = read_parquet(...)` puis `FROM df`). Le chemin peut être local ou
`s3://...` indifféremment, une fois `httpfs` chargé — et accepte un
**motif glob** (`s3://bucket/raw/<flux>/date=*/*.csv`), qui lit et
concatène tous les fichiers correspondants en une seule requête, sans
boucle Python (utilisé dans `transform.py` pour lire toutes les
partitions `date=` d'un flux d'un coup).

`read_csv_auto`/`read_json_auto` **devinent** les types de colonnes à
partir du contenu (d'où le `_auto`) — pas besoin de déclarer un schéma
à l'avance, contrairement à un `CREATE TABLE` classique. `read_json_auto`
a deux formes distinctes selon la forme du JSON source :
- un fichier **liste d'objets** (`[{...}, {...}]`, cas de `rfid_scans.json`) :
  `read_json_auto('chemin')` suffit, chaque objet devient une ligne.
- un fichier **NDJSON** (un objet JSON par ligne, sans `[`/`]`/virgules
  — cas des fichiers déposés par `sse_consumer.py`) : nécessite
  `read_json_auto('chemin', format='newline_delimited')` explicitement,
  sinon DuckDB tente de parser tout le fichier comme un seul document
  JSON et échoue.

**Piège concret rencontré** : le motif glob `raw/<flux>/date=*/*.<ext>`
active automatiquement le *hive partitioning* de DuckDB — le segment
`date=AAAA-MM-JJ` du chemin devient une vraie colonne `date` dans le
résultat, sans l'avoir demandé. Pas un bug : comportement documenté du
moteur, gardé tel quel ici (trace utile la date d'ingestion) plutôt que
supprimé — voir `catalogue_omega_lake.md` §2.

### `DESCRIBE SELECT * FROM <lecture>`
Renvoie le schéma (nom de colonne, type) d'une requête **sans
l'exécuter pour de vrai** — utilisé pour introspecter le schéma réel
d'un fichier Parquet/CSV/JSON dans le catalogue (`catalogue.py`) plutôt
que de le documenter à la main. Chaque ligne du résultat a plus de deux
colonnes (nom, type, nullable, clé, défaut, extra) — d'où le
déballage `for nom, type_, *_ in schema_brut` (le `*_` absorbe le
reste sans le nommer).

### `COPY (<requête>) TO '<chemin>' (FORMAT PARQUET)`
Écrit le résultat d'une requête en Parquet — vers un chemin local ou
`s3://...`. **Réécrit** le contenu (ne préserve pas les octets source
telle quelle) : ne pas utiliser pour une copie fidèle (voir la note
raw/ ci-dessous), seulement pour une vraie transformation.

**Pourquoi pas pandas** : ce projet n'utilise `pandas` nulle part
(vérifié par grep sur tous les notebooks avant d'introduire DuckDB, voir
`integration_infrastructure_omega_lake.md` §1.2) — DuckDB s'utilise en
SQL direct, cohérent avec le reste du projet (`psycopg2` en SQL direct
partout ailleurs), pandas reste optionnel en sortie (`.df()`) si jamais
un notebook en a besoin pour un graphique, mais n'est jamais nécessaire
pour lire/transformer/joindre.

**Pourquoi pas DuckDB pour l'ingestion `raw/`** : lire puis réécrire un
CSV/JSON via DuckDB reformatterait potentiellement le contenu (quotage,
ordre des clés) sans changer l'information — la zone `raw/` du data
lake exige une copie octet pour octet (voir `boto3.upload_file`
ci-dessus, utilisé précisément pour cette raison).

---

## hmac / hashlib (introduit en C21bis)

Modules de la bibliothèque standard — pas de dépendance externe. Utilisés
pour pseudonymiser `vehicule_id` (`curated_bi.py`) sans jamais stocker de
table de correspondance persistante (voir §2 ci-dessous).

### `hmac.new(cle, message, hachage)`
Calcule un **HMAC** (*Hash-based Message Authentication Code*) — pas un
hash simple. Les trois arguments sont positionnels : `cle` et `message`
en `bytes` (`.encode()` depuis une `str`), `hachage` une fonction de la
famille `hashlib` (ici `hashlib.sha256`, passée telle quelle, pas
appelée). `.hexdigest()` sur le résultat donne une chaîne hexadécimale
lisible.

**Le piège que ce projet a failli manquer** : `hashlib.sha256(message)`
seul (sans clé) est un hash, pas un HMAC — déterministe et **public**,
n'importe qui connaissant les valeurs possibles peut le recalculer et
retrouver la correspondance (ce jeu de données ne compte que 15
véhicules : `sha256("VH-001")` à `sha256("VH-015")` suffiraient à tout
retrouver, clé ou pas). `hmac.new(cle, ...)` intègre la clé secrète dans
le calcul selon une construction spécifique (RFC 2104, avec un
remplissage interne/externe) — sans la clé, impossible de recalculer la
même valeur, même en connaissant tous les messages possibles.

Utilisé dans : `src/datacore/storage/lake/curated_bi.py::pseudonyme()`

```python
hmac.new(cle.encode(), vehicule_id.encode(), hashlib.sha256).hexdigest()[:16]
```

**Pourquoi tronquer à 16 caractères** (`[:16]`) : un pseudonyme n'a pas
besoin de la résistance aux collisions complète d'un SHA-256 (64
caractères hex) — 16 caractères hexadécimaux (64 bits) suffisent
largement à distinguer 15 véhicules sans collision, et restent plus
lisibles dans un aperçu de données.

### Pourquoi aucune table de correspondance n'est stockée nulle part

`pseudonyme()` est une fonction **pure** : même entrée + même clé →
toujours la même sortie (propriété de HMAC), donc pas besoin de
mémoriser "VH-001 → d1ddafb..." dans une table persistante pour
retrouver la correspondance plus tard — elle se recalcule à la demande.
`curated_bi.py` crée bien une table temporaire DuckDB
(`CREATE TEMP TABLE`) pendant la construction de l'export, mais elle ne
sert qu'à faire la jointure SQL efficacement ; elle est explicitement
détruite (`DROP TABLE`) à la fin de la fonction, et n'existe jamais en
dehors de cette exécution — rejouée en entier à chaque appel, jamais mise
en cache. Rien à protéger côté stockage : la seule chose qui permettrait
de reconstituer la correspondance est la clé (`LAKE_PSEUDONYM_KEY`),
jamais écrite dans un objet lisible par `lake_reader`.
