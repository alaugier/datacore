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
