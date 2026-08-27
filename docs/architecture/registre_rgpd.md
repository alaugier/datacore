# Registre des traitements de données personnelles — Base de travail

**Compétence couverte : C11 — Créer une base de données**
**Épreuve associée : E4 (mise en situation professionnelle)**

Ce registre opérationnalise la structure cible définie dans
l'[étude technique d'architecture §4](architecture_cible.md#4-mise-en-conformité-rgpd)
(C3) : il s'agit ici d'un registre **réel et versionné**, tenu à jour
pour la base de travail créée en C11 — pas d'une structure prévisionnelle.

## 1. Données personnelles réellement présentes

Vérification exhaustive des colonnes de toutes les sources du programme
(FluxPro, TransFlow, fichiers clients, historique) : **trois colonnes
seulement** contiennent des données à caractère personnel.

| Colonne | Table | Nature | Personne concernée |
|---|---|---|---|
| `chauffeur` | `tournees` | Nom du conducteur (ex. « Yanis L. ») | Salarié d'un transporteur partenaire |
| `adresse_livraison` | `livraisons` | Adresse du destinataire | Client final (destinataire de la marchandise) |
| `contact` | `transporteurs` | Contact professionnel (ex. « contact@rapidfret.example ») | Contact d'entreprise, faible sensibilité |

Aucune donnée personnelle n'a été trouvée dans les tables FluxPro
(`clients`, `produits`, `commandes`, etc. — niveau entreprise, pas
d'individu nommé), ni dans les trois fichiers clients bruts (NordDrive,
FreshMarket, MedioTex — uniquement des données de commande produit).
C'est un résultat positif du point de vue de la minimisation : le
périmètre réel à protéger est restreint et précisément identifié,
plutôt que supposé.

## 2. Registre des traitements

| # | Traitement | Finalité | Base légale | Données concernées | Durée de conservation | Mesures de sécurité |
|---|---|---|---|---|---|---|
| 1 | Suivi des tournées de livraison | Organisation opérationnelle du transport, traçabilité des livraisons | Exécution du contrat de prestation logistique (intérêt légitime) | `tournees.chauffeur` | Durée de la tournée + 12 mois (analyse de performance), puis anonymisation | Accès restreint au groupe Data Engineers (voir §4) ; colonne dédiée, permettant un tri ciblé sans purge de toute la ligne |
| 2 | Livraison des expéditions | Acheminement du colis à la bonne adresse | Exécution du contrat (livraison de marchandise commandée) | `livraisons.adresse_livraison` | Durée de la livraison + 12 mois (litiges éventuels), puis anonymisation | Accès restreint ; pas de diffusion externe hors périmètre du destinataire concerné |
| 3 | Contact des transporteurs partenaires | Relation contractuelle avec les transporteurs | Exécution du contrat avec le transporteur | `transporteurs.contact` | Durée du contrat-cadre avec le transporteur | Donnée professionnelle à faible sensibilité, accès équipe Data + Pilotage |

## 3. Procédures de tri et de purge

Requêtes types, à exécuter dans le cadre d'une revue périodique (voir
cadence dans [`supervision_projet.md`](supervision_projet.md)) :

```sql
-- Anonymisation des tournées de plus de 12 mois (traitement 1)
UPDATE tournees
SET chauffeur = NULL
WHERE date < CURRENT_DATE - INTERVAL '12 months';

-- Anonymisation des adresses de livraison de plus de 12 mois (traitement 2)
-- (jointure via tournees pour dater la livraison, livraisons n'a pas de date propre)
UPDATE livraisons l
SET adresse_livraison = NULL
FROM tournees t
WHERE t.id = l.tournee_id
  AND t.date < CURRENT_DATE - INTERVAL '12 months';
```

**Limite du jeu de données pédagogique** : `livraisons` ne porte pas de
date propre (seulement `heure_estimee`/`heure_reelle`, sans date) — la
purge s'appuie donc sur la date de la tournée associée (`tournees.date`).
En conditions réelles, une date de livraison explicite serait nécessaire
pour une purge précise à l'échelle de la livraison individuelle plutôt
que de la tournée entière.

## 4. Droits d'accès

Reprend le modèle par groupes déjà défini dans l'
[étude technique d'architecture §4.3](architecture_cible.md#43-droits-daccès-par-groupe) :
aucun accès individuel nommé, uniquement par groupe fonctionnel.

| Groupe | Accès à `chauffeur`/`adresse_livraison`/`contact` |
|---|---|
| Data Engineers | Lecture/écriture (nécessaire à la maintenance des pipelines) |
| Data Analysts | Lecture sur données déjà anonymisées/agrégées uniquement (pas d'accès direct aux colonnes personnelles) |
| Référents clients externes | Aucun accès à ces colonnes (hors périmètre de l'API de mise à disposition, C12) |

## 5. Cohérence avec les livrables précédents

Ce registre confirme et précise le principe déjà acté dans
l'[architecture cible](architecture_cible.md) : conformité RGPD *by
design* — les colonnes personnelles ont été identifiées et documentées
dès la modélisation ([`modelisation_merise.md`](modelisation_merise.md)),
avant tout chargement de données réelles dans les tables concernées, pas
en correction a posteriori.
