# Registre RGPD — Data Lake OMEGA LAKE

**Compétence couverte : C21 — Garantir la gouvernance des données**
**Épreuve associée : E7**

Applique au data lake la même discipline que
[`registre_rgpd.md`](registre_rgpd.md) (base de travail, C11) et
[`registre_rgpd_entrepot.md`](registre_rgpd_entrepot.md) (entrepôt,
C16) : un audit **réel et répétable**, pas une conclusion supposée —
à partir de l'inventaire généré par le catalogue (C20).

---

## 1. Résultat de l'audit lexical : aucune colonne directement personnelle

`datacore.governance.audit_rgpd.auditer_lake()` réutilise
`colonnes_suspectes()` (déjà utilisée pour l'entrepôt, C16) sur le
schéma de chaque flux/zone renvoyé par le catalogue — mêmes motifs
(chauffeur/conducteur, adresse, contact, téléphone, email,
prénom/nom complet).

```bash
python3 -m datacore.governance.audit_rgpd
```

Vérifié pour de vrai contre le lake réel (15 entrées, 5 flux × 3
zones) : **aucune colonne suspecte détectée**, entrepôt et lake
confondus (code de sortie 0).

**Ce que cet audit ne couvre pas, volontairement** : la détection est
lexicale (un nom de colonne), pas relationnelle. Elle ne peut pas
repérer un risque de ré-identification qui n'existe qu'en combinant
deux jeux de données — objet du §2.

---

## 2. Traitement identifié : géolocalisation de flotte

**`geoloc_flotte`** (CSV batch) et **`flux_sse_capteurs`** (SSE temps
réel) portent tous deux `vehicule_id`/`lat`/`lon`. Aucun des deux ne
porte de nom de personne — mais `vehicule_id` (`VH-0NN`) se retrouve
aussi dans `tournees.vehicule_id` (base de staging), à côté de
`tournees.chauffeur` (donnée personnelle déjà répertoriée,
[`registre_rgpd.md`](registre_rgpd.md) §1). Le recouvrement temporel
entre les deux jeux de données est **réel**, pas théorique — vérifié en
C18 : `geoloc_flotte` couvre le 01–03/08/2026, `tournees` va jusqu'au
04/08/2026.

Une trace de géolocalisation du lake est donc, en pratique,
ré-identifiable jusqu'au chauffeur par une simple jointure — c'est la
CNIL qui tranche cette qualification pour la géolocalisation de flotte
professionnelle en général : liée à un salarié identifiable, elle est
traitée comme une donnée personnelle, même sans nom explicite dans le
jeu de données lui-même.

| Élément | Valeur |
|---|---|
| Finalité | Suivi opérationnel de la flotte (position, vitesse), amélioration continue |
| Base légale | Intérêt légitime, avec information des salariés concernés (chauffeurs) |
| Mesures de sécurité en place | (1) **Aucune jointure automatisée `vehicule_id` → `chauffeur`** dans le pipeline `curated/` (C18 §6) ; (2) **pseudonymisation HMAC de `vehicule_id`** dans l'export `curated_bi/` exposé à `lake_reader` (§4bis) — défense en profondeur, pas une mesure de plus par principe |
| Durée de conservation | 90 jours pour la donnée brute (`raw/`), purge automatisée — §3 |

### Révision de la position initiale sur la pseudonymisation

Première analyse (C18/C21, avant relecture externe) : pseudonymiser
`vehicule_id` (ex. par un hash) semblait n'apporter aucune protection
réelle, l'argument étant qu'un hash stable resterait tout aussi
joignable qu'un identifiant en clair. **Cet argument était incomplet**,
pas seulement imprécis — il ne valait que pour la population qui a déjà
accès à la fois au lake et à `tournees` en clair (les Data Engineers).
Il ne tenait pas pour `lake_reader` (Data Analysts, accès lake seul,
**sans** accès à la base de staging) : pour cette population, un
pseudonyme HMAC dont la clé de correspondance reste hors de portée
constitue une vraie défense en profondeur — c'est précisément la
définition de la pseudonymisation au sens de l'article 4(5) du RGPD
(protège tant que la clé de ré-identification n'est pas elle-même
compromise).

Revu et corrigé après relecture externe, avec 4 exigences explicites,
toutes vérifiées en conditions réelles :

1. **HMAC à clé secrète, pas un hash simple.** Ce jeu de données ne
   compte que 15 véhicules (`VH-001` à `VH-015`) — un hash sans clé
   serait recalculable par force brute par quiconque connaît cette
   plage (`sha256("VH-001")`, `sha256("VH-002")`, ...). La clé
   (`LAKE_PSEUDONYM_KEY`) n'est jamais distribuée à `lake_reader`.
2. **Mécanisme d'accès de `lake_reader` confirmé avant correction** :
   vérifié que la politique MinIO d'origine (C21) portait sur le bucket
   entier — `lake_reader` pouvait lire `raw/`/`staging/`/`curated/` en
   clair, ce qui aurait rendu une pseudonymisation limitée à un export
   séparé inopérante (contournable en lisant `curated/` directement).
   Corrigé en même temps — §4bis.
3. **Export dédié (`curated_bi/`), `curated/` jamais modifiée** — les
   Data Engineers gardent `vehicule_id` en clair (jointure opérationnelle
   légitime vers `tournees`), seul `lake_reader` voit la version
   pseudonymisée.
4. **Limite assumée, documentée, pas traitée ici** : même
   `vehicule_id` pseudonymisé, une série temporelle de géolocalisation
   dense (1 point/2s, `lat`/`lon`) reste en général ré-identifiable par
   motif de déplacement (domicile, horaires réguliers) — connu dans la
   littérature sur les données de mobilité. La pseudonymisation réduit
   le risque de jointure directe, elle ne l'élimine pas entièrement.

---

## 3. Procédure de purge

`src/datacore/storage/lake/purge.py` — purge les partitions `raw/`
de `geoloc_flotte`/`flux_sse_capteurs` de plus de 90 jours (durée
reprise telle quelle du plan C3), puis reconstruit `staging/`/`curated/`
pour rester cohérent avec `raw/` après coup. Les 3 autres flux (aucune
donnée personnelle, §1) ne sont pas concernés.

```bash
python3 -m datacore.storage.lake.purge
```

**Vérifié en conditions réelles**, pas seulement décrit : une partition
synthétique volontairement datée du 01/01/2026 a été injectée dans
`raw/geoloc_flotte/` (contenu réel, copie d'un fichier source existant,
juste redaté), à côté de la partition réelle du jour. Après exécution :

- La partition ancienne a bien disparu (`1 partition(s) purgée(s)`),
  confirmé indépendamment par une nouvelle liste MinIO (`boto3`, hors du
  processus de purge) — seule la partition du jour reste.
- `flux_sse_capteurs` (aucune partition ancienne) : `0 partition(s)
  purgée(s)` — pas de reconstruction inutile.
- `staging/`/`curated/geoloc_flotte` reconstruits sans erreur (2160
  lignes, cohérent avec le volume réel du flux).

**Limite connue** : si *toutes* les partitions `raw/` d'un flux
venaient à être purgées d'un coup, `staging/`/`curated/` ne seraient pas
automatiquement vidés (la reconstruction est sautée s'il ne reste plus
rien à lire) — cas non rencontré sur ce jeu de données pédagogique (les
partitions réelles n'ont que quelques jours), documenté comme limite
plutôt que traité par du code pour un scénario qui ne se produit pas
ici.

---

## 4. Droits d'accès par groupe

Reprend le modèle par rôle déjà en place pour l'entrepôt (`bi_reader`,
C14/C16) — un utilisateur MinIO dédié, **lecture seule** :

| Élément | Valeur |
|---|---|
| Utilisateur | `lake_reader` (créé automatiquement par le service `minio-init`) |
| Politique | `lake-reader` (`infra/minio/lake-reader-policy.json`) |
| Groupe visé | Data Analysts / consommateurs BI (`architecture_cible.md` §4.3) — pas les Data Engineers, qui gardent l'accès complet via `MINIO_ROOT_USER` pour l'ingestion/les transformations |

**Périmètre de la politique, corrigé après relecture externe** : la
première version (C21) accordait `s3:GetObject`/`s3:ListBucket` sur le
**bucket entier** — vérifié que `lake_reader` pouvait donc lire
`raw/`/`staging/`/`curated/` en clair, pas seulement l'export prévu.
Corrigée pour ne porter que sur `curated_bi/` (§4bis) : `s3:ListBucket`
restreint par une condition `s3:prefix` (`curated_bi/*`), `s3:GetObject`
scopé à `arn:aws:s3:::omega-lake/curated_bi/*` — mêmes principes qu'une
politique IAM S3 standard (condition de préfixe pour le listing,
ressource explicite pour la lecture).

**Vérifié en conditions réelles, avant et après correction** :
- *Avant* : `lake_reader` lisait bien `raw/geoloc_flotte/.../*.csv` en
  clair (`mc cat` a renvoyé le contenu réel, `vehicule_id` inclus) —
  confirme que le risque signalé en relecture externe était réel, pas
  supposé.
- *Après* : `mc ls`/`mc cat` sur `raw/`, `staging/`, `curated/` échouent
  (`Access Denied`) ; `mc ls --recursive` sur `curated_bi/` fonctionne et
  liste les 5 flux.
- **Bout en bout via DuckDB avec les vraies clés `lake_reader`** (pas
  seulement `mc`) : lecture de `curated_bi/geoloc_flotte` réussit et
  renvoie `vehicule_id` pseudonymisé ; la même requête contre
  `curated/geoloc_flotte` échoue avec `HTTP 403 Forbidden`.

Mise en place idempotente : `mc admin policy create`/`mc admin user
add`/`mc admin policy attach` dans le service `minio-init` de
`docker-compose.yml`, revérifiés en relançant `docker compose up`
plusieurs fois sans erreur (y compris après la mise à jour de la
politique — `mc admin policy create` sur un nom existant remplace son
contenu) — même discipline que la création du bucket (C19).

## 4bis. Export pseudonymisé `curated_bi/`

`src/datacore/storage/lake/curated_bi.py` — reconstruit `curated_bi/`
depuis `curated/` pour les 5 flux : copie telle quelle pour les 3 flux
sans géolocalisation, `vehicule_id` remplacé par son pseudonyme HMAC
(`pseudonyme()`, clé `LAKE_PSEUDONYM_KEY`) pour `geoloc_flotte`/
`flux_sse_capteurs`.

```bash
python3 -m datacore.storage.lake.curated_bi
```

**Propriétés vérifiées en conditions réelles** :
- **Stabilité** : `pseudonyme("VH-001")` produit la même valeur dans
  `curated_bi/geoloc_flotte` et `curated_bi/flux_sse_capteurs` —
  continuité analytique préservée (suivre un véhicule dans le temps
  reste possible sans connaître son identifiant réel).
- **Aucune perte de ligne** : mêmes effectifs `curated/`/`curated_bi/`
  pour les 3 flux vérifiés (2160/2160, 6/6, 3000/3000) — la jointure
  contre la table de correspondance ne rejette aucune ligne.
- **`curated/` inchangée** : `vehicule_id` y reste en clair, vérifié en
  relisant `curated/geoloc_flotte` après construction de `curated_bi/`.

---

## 5. Références

- [`architecture_omega_lake.md`](architecture_omega_lake.md) §6 —
  découverte initiale du risque de ré-identification (C18).
- [`architecture_cible.md`](architecture_cible.md) §4.2/§4.3 — plan de
  gouvernance initial (C3), revu au §2 après relecture externe.
- [`registre_rgpd.md`](registre_rgpd.md) — `tournees.chauffeur`, la
  donnée personnelle réelle du programme.
- [`registre_rgpd_entrepot.md`](registre_rgpd_entrepot.md) — même
  discipline d'audit appliquée à l'entrepôt (C16).
- [`catalogue_omega_lake.md`](catalogue_omega_lake.md) — inventaire
  généré dont ce registre dépend (C20).
