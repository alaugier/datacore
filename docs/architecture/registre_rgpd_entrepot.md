# Registre RGPD — Entrepôt OMEGA BI

**Compétence couverte : C16 — Assurer la gestion opérationnelle d'un environnement de données**
**Épreuve associée : E6**

Ce registre applique à l'entrepôt OMEGA BI la même discipline que
[`registre_rgpd.md`](registre_rgpd.md) (base de travail, C11) : un audit
**réel et répétable**, pas une conclusion supposée.

---

## 1. Résultat de l'audit : aucune donnée personnelle

Vérification exhaustive des colonnes des 10 tables/vues de l'entrepôt
(4 schémas Postgres) :

| Table | Colonnes | Donnée personnelle ? |
|---|---|---|
| `dimensions.dim_client` | client_key, client_id, code, nom, secteur, valid_from, valid_to, is_current | Non — `nom` désigne une entreprise cliente (NordDrive, FreshMarket, MedioTex), pas une personne physique |
| `dimensions.dim_site` | site_key, entrepot_id, code, nom, ville, capacite_palettes | Non — entrepôt, pas une personne |
| `dimensions.dim_categorie` | categorie_key, libelle | Non |
| `dimensions.dim_produit` | produit_key, produit_id, sku, libelle, poids_kg, temperature_dirigee, categorie_key | Non |
| `dimensions.dim_temps` | date_key, date_complete, annee, trimestre, mois, nom_mois, jour_semaine, numero_semaine, est_weekend | Non — dimension calendaire générée |
| `dimensions.dim_transporteur` | transporteur_key, transporteur_id, nom | Non — nom de l'entreprise transporteur (RapidFret, EcoRoute...), **`contact` volontairement exclu** dès C13 (voir §2) |
| `exploitation.fait_expedition` | ..., tracking_number, source_systeme, poids_kg, delai_livraison_jours, cout_transport_eur, statut, livre_a_lheure | Non |
| `exploitation.fait_stock` | site_key, produit_key, date_key, quantite_stock | Non |
| `commercial.fait_commande` | ..., commande_id, quantite_commandee, poids_ligne, statut_commande | Non |
| `gouvernance.journal_operations` | id, operation, demarre_le, termine_le, statut, details, erreur | Non — métadonnées d'exécution de pipeline |

**Conclusion : l'entrepôt OMEGA BI ne contient aucune donnée à
caractère personnel.** Ni `tournees.chauffeur`, ni
`livraisons.adresse_livraison`, ni `transporteurs.contact` — les trois
seules données personnelles du programme (base de travail, C11) — n'ont
jamais été chargées dans l'entrepôt. Ce n'est pas un hasard : c'est le
résultat direct des choix RGPD *by design* pris dès la modélisation
(C13, `modelisation_omega_bi.md` §6.5) — ne pas faire transiter vers
l'entrepôt une donnée personnelle dont aucune analyse décisionnelle
n'a besoin, plutôt que de la filtrer après coup.

## 2. Audit répétable, pas une conclusion figée

Un audit ponctuel documenté ici resterait vrai le jour de sa rédaction,
mais silencieux si un futur changement de schéma introduisait une
colonne personnelle sans revue. C'est pourquoi cette conclusion est
appuyée par un **contrôle automatisable** :
[`datacore.governance.audit_rgpd`](../../src/datacore/governance/audit_rgpd.py) —
introspecte `information_schema.columns` des 4 schémas de l'entrepôt et
signale toute colonne dont le nom évoque une donnée personnelle
(motifs : chauffeur/conducteur, adresse, contact, téléphone, email,
prénom/nom complet — les mêmes catégories que celles réellement trouvées
en C11). `nom`/`libelle` seuls ne sont volontairement **pas** suspects :
ce sont des noms d'entités (client, site, transporteur, catégorie), pas
de personnes.

```bash
python3 -m datacore.governance.audit_rgpd
```

Vérifié pour de vrai contre l'entrepôt réel : **aucune colonne
suspecte détectée** (code de sortie 0). Le mécanisme de détection
lui-même a été vérifié séparément contre les noms de colonnes déjà
connus comme personnels dans la base de travail
(`chauffeur`/`adresse_livraison`/`contact`) — correctement signalées —
pour écarter un simple faux négatif silencieux.

À exécuter à chaque revue périodique (même cadence que le registre RGPD
de la base de travail, voir `supervision_projet.md`), et idéalement à
chaque migration Alembic ajoutant une colonne à l'entrepôt.

## 3. Procédure de tri des données personnelles

Puisqu'aucune donnée personnelle n'est présente, il n'y a **rien à
purger** dans l'entrepôt au sens du registre de la base de travail (pas
d'équivalent aux requêtes d'anonymisation de `registre_rgpd.md` §3). La
« procédure de tri » se limite donc, à ce stade, au contrôle
automatisé du §2 — une garde qui empêche une régression silencieuse,
plutôt qu'une purge qui n'aurait rien à traiter.

**Point de vigilance spécifique à l'historisation (C17)** : c'était la
raison de traiter C17 avant C16 (voir `sequencement_bloc3.md` §2.2).
`dimensions.dim_client` accumule désormais plusieurs versions par
client au fil du temps. Ces versions ne sont **pas** des données
personnelles (toujours des attributs d'entreprise — nom, secteur), donc
aucune obligation RGPD de purge ne s'applique à leur profondeur
historique. Une politique de rétention pourrait néanmoins se justifier
un jour pour des raisons d'hygiène de stockage (pas de raison RGPD) —
non nécessaire à ce stade : la table reste de taille modeste (4 lignes
pour 3 clients après le changement démontré en C17), à revisiter si le
volume grandissait significativement.

## 4. Droits d'accès

Reprend le modèle par rôle déjà en place (C14,
`creation_entrepot_omega_bi.md` §4) : `bi_reader` en lecture seule sur
`dimensions`/`exploitation`/`commercial`. **`gouvernance` n'est
délibérément pas accordé à `bi_reader`** : le journal des opérations est
une préoccupation d'exploitation technique, pas un objet d'analyse
métier — accès restreint à l'équipe Data Engineering (connexion
`datacore`, propriétaire du schéma), vérifié pour de vrai (`\dp
gouvernance.journal_operations` ne montre aucun droit accordé à
`bi_reader`).

---

## 5. Références

- [`registre_rgpd.md`](registre_rgpd.md) — registre RGPD de la base de
  travail (C11), les 3 données personnelles réelles du programme.
- [`modelisation_omega_bi.md`](modelisation_omega_bi.md) §6.5 — décision
  RGPD *by design* d'exclure `transporteurs.contact` dès C13.
- [`gestion_operationnelle_omega_bi.md`](gestion_operationnelle_omega_bi.md) —
  premier volet de C16 (sauvegardes, journalisation, tableau de bord).
- [`historisation_dim_client_scd2.md`](historisation_dim_client_scd2.md) —
  C17, à l'origine du point de vigilance du §3.
- [`sql/schema_entrepot_omega_bi.sql`](../../sql/schema_entrepot_omega_bi.sql) —
  schéma SQL brut complet des 10 tables/vues auditées en §1.
