# Historisation de Dim_Client — variation de dimension type 2 (SCD2)

**Compétence couverte : C17 — Mettre en œuvre une variation de dimension**
**Épreuve associée : E6**

Ce document décrit l'historisation de `dimensions.dim_client` selon la
méthode Kimball SCD2 (Slowly Changing Dimension, type 2) : les
changements sur les attributs suivis produisent une **nouvelle ligne**
plutôt que d'écraser l'existante, ce qui préserve l'état historique.

---

## 1. Écart avec la description initiale de l'issue

L'issue #48 mentionne l'historisation « des changements d'adresse ou de
contrat client ». Le jeu de données pédagogique ne porte ni l'un ni
l'autre : `clients` (FluxPro, `data/raw/schema.sql`) ne contient que
`id`, `code`, `nom`, `secteur`. Aucune autre table du programme ne porte
d'adresse ou de contrat au niveau du client (`livraisons.adresse_livraison`
existe, mais c'est l'adresse du destinataire d'une livraison, pas celle
du client lui-même — une entité différente).

**Attributs suivis ici : `nom` et `secteur`.** Ce sont les deux seuls
attributs descriptifs réellement présents sur `clients`, et ce sont des
cas d'usage SCD2 légitimes en soi (renommage/rebranding d'un client,
reclassification sectorielle) — `code`, clé métier stable, n'est
volontairement pas suivi. Décision confirmée avec l'utilisateur avant
implémentation plutôt que supposée.

---

## 2. Mécanisme

`dimensions.dim_client` gagne 3 colonnes (migration additive, voir §3) :

| Colonne | Rôle |
|---|---|
| `valid_from` | Date de début de validité de cette version |
| `valid_to` | Date de fin de validité — `NULL` si version courante |
| `is_current` | `true` sur la version actuellement en vigueur |

`client_key` (clé de substitution posée dès C13, voir
`modelisation_omega_bi.md` §6.1) rend cet ajout possible sans refonte :
un même `client_id` (clé naturelle FluxPro) peut désormais correspondre
à **plusieurs** `client_key`, une par version historisée.

**À chaque exécution du pipeline** (`load_dim_client`, dans
`load_warehouse.py`) :

1. Le client est comparé à sa version courante déjà en base
   (`is_current = true`).
2. **Client inédit** (aucune version courante) : insertion directe.
3. **Aucun changement** (`nom`/`secteur` identiques) : la ligne
   existante est réutilisée, rien n'est écrit.
4. **Changement détecté** : la version courante est close
   (`valid_to` = date du jour, `is_current = false`), puis une nouvelle
   ligne est insérée (nouvelle `client_key`, `valid_from` = date du jour,
   `is_current = true`).

**`Dim_Client` n'est jamais tronquée** par le pipeline (`truncate_warehouse`),
contrairement aux 7 autres tables alimentées par C15 — une troncature
détruirait l'historique accumulé au fil des exécutions. Les tables de
faits, elles, restent rechargées en entier à chaque exécution et
référencent donc systématiquement la version **courante** du client :
ce pipeline ne reconstruit pas rétroactivement quelle version de
`Dim_Client` était en vigueur au moment de chaque fait passé — seule
`Dim_Client` elle-même conserve une vraie profondeur historique.

---

## 3. Garantie d'intégrité en base : index unique partiel

Le mécanisme applicatif décrit en §2 (comparaison à la version courante
avant écriture) empêche `load_dim_client` de créer un doublon dans son
propre déroulement normal — mais rien, initialement, n'empêchait en
base une seconde ligne `is_current = true` pour le même `client_id` : ni
exécution concurrente du pipeline, ni script de correction manuelle, ni
insertion directe n'auraient déclenché la moindre erreur Postgres. Point
relevé en revue externe du compte rendu M2, vérifié avant correction
(aucune contrainte de ce type n'existait sur `dim_client`, confirmé par
`\d dimensions.dim_client`) plutôt que pris pour argent comptant.

Corrigé par un **index unique partiel** (migration `44a800999124`,
additive) :

```sql
CREATE UNIQUE INDEX uq_dim_client_courant
ON dimensions.dim_client (client_id)
WHERE is_current;
```

Un doublon `is_current = true` sur un même `client_id` est désormais
rejeté par Postgres lui-même, quelle que soit la voie d'écriture — pas
seulement par la logique de `load_dim_client`. Une ligne historique
(`is_current = false`) partageant le même `client_id` qu'une autre reste
autorisée, comme attendu.

**`load_dim_client` traduit une violation de cet index en erreur
explicite** plutôt que de laisser remonter la trace psycopg2 brute :

```python
except psycopg2.errors.UniqueViolation as exc:
    raise RuntimeError(
        f"Conflit SCD2 sur dim_client : une version courante existe "
        f"déjà pour client_id={r['id']} (contrainte "
        f"uq_dim_client_courant) -- exécution concurrente du "
        f"pipeline ou écriture directe en base ?"
    ) from exc
```

Vérifié pour de vrai contre l'entrepôt réel : l'index accepte les 4
lignes déjà en place sans conflit à sa création ; une tentative
d'insertion manuelle d'un second `is_current = true` pour `client_id = 1`
est rejetée (`ERROR: duplicate key value violates unique constraint`) ;
une insertion `is_current = false` pour ce même `client_id` reste
acceptée.

---

## 4. Migrations

Deux migrations additives.

**Première**
(`src/datacore/storage/warehouse/migrations/versions/ad009b506239_*.py`) :
colonnes ajoutées nullables d'abord (Postgres refuse un `ADD COLUMN NOT
NULL` sans défaut sur une table déjà peuplée — `dim_client` portait déjà
3 lignes, chargées par C15), backfill explicite des lignes existantes
(`valid_from = 2022-01-01`, même ancre que `DATE_DEBUT` dans
`load_dim_temps.py` — « début de l'historique connu » — `is_current =
true`), puis passage en `NOT NULL`.

**Bug latent corrigé au passage** : `env.py` de l'environnement Alembic
de l'entrepôt ne passait pas `include_schemas=True` à
`context.configure()`. Sans ce paramètre, l'autogénération ne reflète
que le schéma `public` par défaut — invisible pour des tables vivant
dans `dimensions`/`exploitation`/`commercial`, elle proposait donc de
**recréer les 9 tables existantes** au lieu de ne détecter que les 3
colonnes réellement nouvelles. Passé inaperçu pour la migration initiale
de C14 (créer un entrepôt vide depuis rien donnait, par coïncidence, le
même résultat), révélé par cette seconde migration. Corrigé dans les
deux fonctions `run_migrations_*` de `env.py`.

**Seconde**
(`src/datacore/storage/warehouse/migrations/versions/44a800999124_*.py`) :
ajoute l'index unique partiel décrit en §3, suite à la revue externe du
compte rendu M2. Cycle `downgrade`/`upgrade` retesté après ajout.

---

## 5. Procédure de test

**Tests unitaires** (`tests/unit/test_load_warehouse.py`) : trois cas
avec un curseur factice dédié (`FakeScd2Cursor`, simule le
SELECT-puis-branche propre au SCD2) — client inédit (insertion simple,
pas de clôture), version inchangée (réutilisation, aucune écriture),
changement détecté (clôture + nouvelle ligne, nouvelle `client_key`
retournée). Un quatrième cas couvre l'index unique partiel de §3
(`test_load_dim_client_violation_index_leve_une_erreur_explicite`) :
`FakeScd2Cursor` simule un `psycopg2.errors.UniqueViolation` sur
l'`INSERT` dans `dim_client`, et le test vérifie que `load_dim_client`
le traduit bien en `RuntimeError` explicite (message contenant le
`client_id` en cause), avec l'exception d'origine préservée via
`__cause__`.

**Vérification live** (Docker Compose) de l'index et de la gestion
d'erreur : migration `44a800999124` appliquée contre l'entrepôt réel
peuplé (4 lignes existantes, aucun conflit à la création de l'index) ;
tentative d'insertion manuelle d'un second `is_current = true` pour un
`client_id` déjà courant rejetée par Postgres ; insertion d'une ligne
`is_current = false` pour ce même `client_id` acceptée ; cycle complet
`downgrade`/`upgrade` rejoué sans erreur.

**Test de bout en bout réel** (Docker Compose), effectué lors de la
création de ce livrable — le jeu de données pédagogique étant statique
(`clients.csv` ne change jamais entre deux exécutions), un changement a
été **simulé délibérément** pour prouver le mécanisme, pas observé
naturellement :

```sql
-- Simulation d'une évolution réelle de NordDrive
UPDATE clients SET secteur = 'Pieces automobiles et electromobilite'
WHERE code = 'NORDDRIVE';
```

Résultat après réexécution du pipeline :

| client_key | client_id | nom | secteur | valid_from | valid_to | is_current |
|---|---|---|---|---|---|---|
| 4 | 1 | NordDrive | Pieces automobiles | 2022-01-01 | 2026-09-21 | **false** |
| 7 | 1 | NordDrive | Pieces automobiles et electromobilite | 2026-09-21 | — | **true** |
| 5 | 2 | FreshMarket | Grande distribution alimentaire | 2022-01-01 | — | true |
| 6 | 3 | MedioTex | Textile | 2022-01-01 | — | true |

Vérifié : l'ancienne version (`client_key = 4`) reste présente et
interrogeable (historique préservé, pas écrasé) ; les deux autres
clients, non modifiés, n'ont produit aucune ligne supplémentaire (pas de
sur-versionnement) ; `commercial.fait_commande` référence bien la
nouvelle `client_key` courante (7) après le rechargement, pas l'ancienne.
Rejoué une seconde fois sans nouveau changement staging : aucune ligne
supplémentaire créée (idempotence confirmée sur le cas « inchangé »).

---

## 6. Références

- [`modelisation_omega_bi.md`](modelisation_omega_bi.md) §6.1 — décision
  de poser la clé de substitution dès C13 pour anticiper cet ajout.
- [`sequencement_bloc3.md`](sequencement_bloc3.md) §2 — justification de
  l'ordre C17 avant C16 (la procédure de purge RGPD de C16 dépend de ce
  schéma historisé).
- [`pipelines_etl_omega_bi.md`](pipelines_etl_omega_bi.md) — pipeline
  ETL modifié par cette livraison (C15).
