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
| Mesure de sécurité déjà en place | **Aucune jointure automatisée `vehicule_id` → `chauffeur`** dans le pipeline curated (décision de conception, C18 §6 — la mesure porte sur le risque réel identifié, pas sur `vehicule_id` isolément) |
| Durée de conservation | 90 jours pour la donnée brute (`raw/`), purge automatisée — §3 |

### Écart assumé par rapport au plan initial de C3

L'étude d'architecture cible (`architecture_cible.md` §4.2, rédigée
avant que la moindre donnée réelle ne soit manipulée) envisageait une
« pseudonymisation des identifiants véhicule/chauffeur ». Une fois
l'analyse réelle faite en C18, ce n'est **pas** ce qui a été retenu :
pseudonymiser `vehicule_id` (ex. le remplacer par un hash) n'apporterait
aucune protection réelle — l'identifiant reste nécessaire au suivi
opérationnel légitime de la flotte, et un hash stable serait tout aussi
ré-identifiable par jointure qu'un identifiant en clair. La vraie mesure
de protection est **l'absence de la jointure elle-même**, pas
l'obfuscation d'une clé qui doit rester exploitable. Écart documenté
plutôt que silencieusement abandonné : le plan initial visait le bon
risque avec la mauvaise mesure.

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
| Politique | `lake-reader` (`infra/minio/lake-reader-policy.json`) : `s3:GetObject`, `s3:ListBucket` uniquement |
| Groupe visé | Data Analysts / consommateurs BI (`architecture_cible.md` §4.3) — pas les Data Engineers, qui gardent l'accès complet via `MINIO_ROOT_USER` pour l'ingestion/les transformations |

**Vérifié en conditions réelles** : avec l'utilisateur `lake_reader`,
`mc ls` sur le bucket fonctionne (lecture confirmée) ; une tentative
d'upload (`mc cp`) échoue avec `Insufficient permissions to access this
path` — l'écriture est bien refusée, pas seulement supposée absente de
la politique.

Mise en place idempotente : `mc admin policy create`/`mc admin user
add`/`mc admin policy attach` dans le service `minio-init` de
`docker-compose.yml`, revérifiés en relançant `docker compose up` deux
fois de suite sans erreur — même discipline que la création du bucket
(C19).

---

## 5. Références

- [`architecture_omega_lake.md`](architecture_omega_lake.md) §6 —
  découverte initiale du risque de ré-identification (C18).
- [`architecture_cible.md`](architecture_cible.md) §4.2/§4.3 — plan de
  gouvernance initial (C3), dont le §2 documente l'écart assumé.
- [`registre_rgpd.md`](registre_rgpd.md) — `tournees.chauffeur`, la
  donnée personnelle réelle du programme.
- [`registre_rgpd_entrepot.md`](registre_rgpd_entrepot.md) — même
  discipline d'audit appliquée à l'entrepôt (C16).
- [`catalogue_omega_lake.md`](catalogue_omega_lake.md) — inventaire
  généré dont ce registre dépend (C20).
