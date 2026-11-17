# Notes de syntaxe Python — structures imbriquées (préparation orale)

**But** : décomposer, ligne par ligne, quelques expressions Python denses
du dépôt — plusieurs appels/opérations imbriqués sur une seule ligne —
pour pouvoir les expliquer sans hésiter si le jury pointe une ligne au
hasard. Chaque exemple cite le fichier réel, puis se décompose de
l'intérieur vers l'extérieur avec un mini-exemple autonome (valeurs
inventées, à rejouer dans un terminal Python si besoin). Liste non
exhaustive — le réflexe à avoir le jour J : repérer la fonction la plus
*intérieure* (celle qui s'exécute en premier), dérouler vers l'extérieur.

---

## 1. `dict(zip(columns, row, strict=True))` dans une compréhension de liste

Cité tel quel dans [`src/datacore/ingestion/fluxpro.py:67`](../../src/datacore/ingestion/fluxpro.py) (et deux fois dans `src/datacore/api/repository.py`) :

```python
columns = [desc[0] for desc in cursor.description]
return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
```

**Le problème que ça résout** : `cursor.fetchall()` (psycopg2) renvoie
des lignes comme des **tuples positionnels**, sans nom de colonne —
`(1, 'Paris', 75000)`, pas `{"id": 1, "ville": "Paris", ...}`. Il faut
donc ré-associer chaque valeur à son nom de colonne.

**Décomposition, dans l'ordre d'exécution réel** (l'intérieur d'abord) :

1. `columns` est déjà construit avant, à partir de `cursor.description`
   (métadonnées de la requête) : `["id", "ville", "code_postal"]`.
2. `cursor.fetchall()` renvoie la liste des lignes brutes :
   `[(1, "Paris", 75000), (2, "Lyon", 69000)]`.
3. Pour **une** ligne `row` (ex. `(1, "Paris", 75000)`), `zip(columns, row, strict=True)` les apparie position par position : ça produit un flux de paires `("id", 1), ("ville", "Paris"), ("code_postal", 75000)`.
4. `dict(...)` sur ce flux de paires construit
   `{"id": 1, "ville": "Paris", "code_postal": 75000}`.
5. Le `[... for row in cursor.fetchall()]` autour répète les étapes 3-4
   pour **chaque** ligne, et donne la liste complète de dicts.

**Mini-exemple autonome** :
```python
>>> columns = ["id", "ville"]
>>> rows = [(1, "Paris"), (2, "Lyon")]
>>> [dict(zip(columns, row, strict=True)) for row in rows]
[{'id': 1, 'ville': 'Paris'}, {'id': 2, 'ville': 'Lyon'}]
```

**Pourquoi `strict=True`** (le détail qui compte) : sans lui, `zip()`
s'arrête silencieusement dès que l'un des deux côtés est épuisé — si
`columns` a 3 noms mais qu'une ligne n'en a que 2 (bug de schéma,
décalage), le résultat serait tronqué *sans erreur*, un bug silencieux
difficile à repérer. Avec `strict=True`, une longueur différente lève
immédiatement une `ValueError` — on préfère une erreur visible à une
donnée fausse.

---

## 2. `json.dump(records, f, ensure_ascii=False, indent=2, default=_json_default)`

Cité dans [`src/datacore/ingestion/landing.py:51`](../../src/datacore/ingestion/landing.py) :

```python
with open(path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2, default=_json_default)
```

**Décomposition, un paramètre à la fois** :
- `records, f` : l'objet à écrire (une liste de dicts), et le fichier
  déjà ouvert en écriture où l'écrire.
- `ensure_ascii=False` : par défaut, `json.dump` échappe tout caractère
  non-ASCII (`é` deviendrait `é` dans le fichier) — mis à `False`,
  les accents restent lisibles tels quels.
- `indent=2` : écrit le JSON sur plusieurs lignes avec 2 espaces
  d'indentation, lisible à l'œil, plutôt qu'une seule ligne compacte.
- `default=_json_default` : le point le plus intéressant, voir
  ci-dessous.

**Le rôle de `default=`** : `json.dump` sait nativement sérialiser un
nombre restreint de types Python (`str`, `int`, `float`, `bool`,
`None`, `list`, `dict`). Mais `cursor.fetchall()` (psycopg2) renvoie
parfois des types Python *qui ne sont pas dans cette liste* — un
`decimal.Decimal` pour une colonne `NUMERIC`, un `datetime.date` pour
une colonne `DATE`. Quand `json.dump` rencontre une valeur qu'il ne
reconnaît pas, **il appelle la fonction passée en `default=` avec
cette valeur**, et utilise ce qu'elle renvoie à la place :

```python
def _json_default(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    raise TypeError(f"non sérialisable : {value!r}")
```

**Mini-exemple autonome** :
```python
>>> import json, datetime, decimal
>>> data = {"prix": decimal.Decimal("19.90"), "date": datetime.date(2026, 11, 17)}
>>> json.dumps(data, default=_json_default)
'{"prix": 19.9, "date": "2026-11-17"}'
```

**Pourquoi `Decimal` et pas juste `float` dès la requête SQL** : une
colonne `NUMERIC`/`DECIMAL` existe justement pour éviter les erreurs
d'arrondi binaire du `float` (ex. `0.1 + 0.2 != 0.3` en `float`) — SQL
et psycopg2 préservent cette précision exacte jusqu'au bout. JSON, lui,
n'a qu'un seul type numérique ; la conversion en `float` au moment de
l'écriture JSON est un choix assumé (perte de précision acceptable pour
un fichier d'atterrissage intermédiaire, pas pour un calcul financier).

---

## 3. `list(csv.DictReader(f, delimiter=","))`

Cité dans [`src/datacore/ingestion/historique.py:24`](../../src/datacore/ingestion/historique.py) et
[`src/datacore/ingestion/clients_files.py:27`](../../src/datacore/ingestion/clients_files.py) :

```python
with open(path, encoding="utf-8", newline="") as f:
    return list(csv.DictReader(f, delimiter=delimiter))
```

**Décomposition** :
- `csv.DictReader(f, delimiter=",")` enveloppe le fichier ouvert `f` :
  il lit la **première ligne** comme des noms de colonnes (l'en-tête),
  et transforme chaque ligne suivante en dict `{nom_colonne: valeur}`.
  `delimiter=","` précise le séparateur (certains exports Excel
  français utilisent `;` à la place — paramétrable pour ça).
- `csv.DictReader(...)` seul est un **itérateur paresseux** : il ne lit
  pas tout le fichier d'un coup, seulement ligne par ligne, à la
  demande.
- `list(...)` force la lecture immédiate de **tout** le fichier
  maintenant, et construit la liste complète de dicts en mémoire.

**Mini-exemple autonome** :
```python
>>> import csv, io
>>> texte = "nom,ville\nDupont,Paris\nMartin,Lyon\n"
>>> list(csv.DictReader(io.StringIO(texte), delimiter=","))
[{'nom': 'Dupont', 'ville': 'Paris'}, {'nom': 'Martin', 'ville': 'Lyon'}]
```

**Pourquoi `list(...)` est indispensable ici, pas juste une habitude** :
le `with open(path) as f: ...` ferme le fichier `f` dès la sortie du
bloc `with` — qui arrive juste après le `return`. Si on renvoyait
`csv.DictReader(f)` tel quel (sans `list()`), l'appelant recevrait un
itérateur encore lié à `f`, mais `f` serait déjà fermé au moment où il
essaierait de s'en servir : plus aucune ligne ne serait lisible.
`list(...)` consomme l'itérateur et capture toutes les lignes en
mémoire *pendant que le fichier est encore ouvert*, avant le `return`.

---

## 4. (bonus) Enchaînement de méthodes sur une ligne

Cité dans [`src/datacore/ingestion/portail_scraping.py:29`](../../src/datacore/ingestion/portail_scraping.py) :

```python
return [str(a["href"]).rsplit("/", 1)[-1] for a in links]
```

**Décomposition, de gauche à droite (chaque résultat nourrit l'étape suivante)** :
1. `a["href"]` : récupère l'attribut HTML `href` d'un lien scrapé
   (BeautifulSoup) — ex. `"/portail-transporteur/colis/COL-00042"`.
2. `str(...)` : garantit que c'est bien une chaîne de caractères Python
   (sécurité de typage, l'attribut l'est déjà en pratique ici).
3. `.rsplit("/", 1)` : découpe la chaîne en partant de la **droite**,
   au maximum 1 fois, sur `"/"` → `["/portail-transporteur/colis", "COL-00042"]`.
4. `[-1]` : prend le **dernier** élément de cette liste de 2 →
   `"COL-00042"`.

**Mini-exemple autonome** :
```python
>>> href = "/portail-transporteur/colis/COL-00042"
>>> str(href).rsplit("/", 1)[-1]
'COL-00042'
```

**Pourquoi `rsplit` (depuis la droite) plutôt que `split`** : l'objectif
est d'isoler le **dernier segment** du chemin (l'identifiant), quelle
que soit la profondeur du reste de l'URL — `rsplit(..., 1)` s'arrête dès
qu'il a trouvé ce dernier séparateur, sans avoir besoin de découper
toute la chaîne en morceaux inutiles.

---

## 5. (bonus) Déballer un tuple à un seul élément dans une boucle

Cité dans [`src/datacore/storage/lake/curated_bi.py:164`](../../src/datacore/storage/lake/curated_bi.py) :

```python
correspondance = [(vehicule_id, pseudonyme(vehicule_id)) for (vehicule_id,) in identifiants]
```

**Le piège à repérer** : `identifiants` vient d'une requête SQL
(`SELECT DISTINCT vehicule_id FROM ...`) — psycopg2 renvoie **toujours**
des lignes sous forme de tuples, même pour une seule colonne :
`[("VH-001",), ("VH-002",), ...]` (remarquer la virgule après
`"VH-001"` : c'est un tuple à 1 élément, pas juste des parenthèses).

**Décomposition** :
- `for (vehicule_id,) in identifiants` : la virgule dans `(vehicule_id,)`
  est **obligatoire** — elle dit à Python « déballe ce tuple à 1 élément
  directement dans la variable `vehicule_id` », plutôt que d'écrire
  `vehicule_id = row[0]` sur une ligne séparée à chaque itération.
- `pseudonyme(vehicule_id)` : calcule le hash HMAC de cet identifiant
  (voir la slide C21 sur la pseudonymisation).
- `(vehicule_id, pseudonyme(vehicule_id))` : construit une **paire**
  (identifiant réel, son pseudonyme).
- Le tout dans `[...]` : une liste de ces paires, pour construire une
  table de correspondance réel → pseudonyme.

**Mini-exemple autonome** :
```python
>>> identifiants = [("VH-001",), ("VH-002",)]
>>> [(vid, vid.lower()) for (vid,) in identifiants]
[('VH-001', 'vh-001'), ('VH-002', 'vh-002')]
```

**Si la virgule est oubliée** (`for (vehicule_id) in identifiants`,
sans virgule) : ce n'est plus un motif de déballage, juste des
parenthèses autour d'un nom — `vehicule_id` vaudrait alors le tuple
entier `("VH-001",)`, pas la chaîne `"VH-001"` — une erreur subtile,
sans message d'erreur immédiat, qui ne se verrait qu'au résultat final.

---

## Repère général pour lire une ligne dense à l'oral

Si le jury pointe une ligne imbriquée non listée ici : annoncer qu'on
va la lire « de l'intérieur vers l'extérieur » (l'appel le plus
profond s'exécute en premier), nommer chaque étape à voix haute, puis
donner un petit exemple chiffré sur le papier/tableau si besoin — exactement
la méthode utilisée dans ce document.
