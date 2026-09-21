# Séquencement du Bloc 4 — confirmation de l'ordre C18 à C21

Note courte, sur le même principe que
[`sequencement_bloc3.md`](sequencement_bloc3.md) : contrairement au Bloc 3
(où le couple C16/C17 méritait d'être inversé par rapport au Gantt),
l'ordre C18 → C19 → C20 → C21 du
[Gantt](feuille_de_route.md#41-diagramme-de-gantt) (§4.1, Phase 4) ne fait
pas débat ici — vérifié avant de le confirmer, pas supposé.

---

## 1. Point de départ : les données IoT sont déjà présentes et réelles

Contrairement à ce que suggère « anticipation du bloc 4 » dans
[`topographie_donnees.md` §3.5](topographie_donnees.md#35-données-iot-anticipation-du-bloc-4--data-lake-omega-lake),
les 5 flux documentés sont déjà dans le dépôt, volumétrie vérifiée pour de
vrai (comptage direct, pas repris du document) :

| Fichier / flux | Lignes de données réelles |
|---|---|
| `data/raw/iot/capteurs_temperature.csv` | 2592 |
| `data/raw/iot/geoloc_flotte.csv` | 2160 |
| `data/raw/iot/camera_comptage.csv` | 432 |
| `data/raw/iot/rfid_scans.json` | 3000 entrées |
| `/api/stream/capteurs` (api-mock, SSE) | continu, 1 évènement / 2 s |

Les 4 volumétries CSV/JSON correspondent exactement aux chiffres déjà
documentés en C2 — aucune correction nécessaire, contrairement à ce
qu'avait révélé la vérification équivalente en C15/M2 (§`schema_*.sql`).
Le flux SSE réel (`api-mock/app.py`) diffuse `timestamp`, `entrepot`,
`zone`, `temperature_c`, `vehicule_id`, `lat`, `lon` — cohérent avec la
description de C3.

---

## 2. C18 → C19 → C20 → C21 : confirmé sans réserve

| Étape | Dépend de | Raison |
|---|---|---|
| C18 — Architecture du data lake | Choix de principe déjà posés en C3 (zones `raw`/`staging`/`curated`, `architecture_cible.md` §2.2) | Reste à arrêter les décisions concrètes propres au Bloc 4 : organisation exacte des zones pour ces 5 flux précis, et surtout comment le data lake s'articule avec le staging/l'entrepôt déjà en place — point explicitement laissé ouvert dans [`M2.md` §5](../comptes_rendus/M2.md) (flux séparé ou alimentation croisée). On ne peut pas intégrer une infrastructure dont la cible n'est pas encore arrêtée. |
| C19 — Intégration infrastructure | Architecture C18 arrêtée | Installer/connecter des composants (stockage objet, consommateur du flux SSE, ingestion batch des 4 fichiers) suppose de savoir dans quelles zones et selon quel schéma ils atterrissent — c'est l'objet même de C18. |
| C20 — Catalogue de données | Données réellement présentes dans le lake (C19) | On ne catalogue pas un contenu qui n'existe pas encore physiquement ; cataloguer après ingestion, pas avant, évite un catalogue théorique déconnecté de ce qui est réellement chargé. |
| C21 — Gouvernance des données | Catalogue C20 disponible | La gouvernance (registre RGPD renforcé, droits d'accès) doit s'appuyer sur un inventaire réel des champs sensibles (`geoloc_flotte.vehicule_id`/`lat`/`lon`, le flux SSE reprenant les mêmes coordonnées géolocalisées) — le catalogue de C20 est ce qui permet d'identifier précisément quoi gouverner, plutôt que de statuer à l'aveugle. Même logique que la dépendance C13→C16 confirmée en Bloc 3 (gouverner après avoir vu le schéma réel, pas avant). |

Aucune alternative sérieuse : concevoir avant d'intégrer, intégrer avant
de cataloguer, cataloguer avant de gouverner. Le Gantt (C18 7j → C19 10j
→ C20 7j → C21 7j, séquentiel) reflète cette contrainte, comme en Bloc 3.

**Point de vigilance RGPD identifié dès maintenant** (à traiter en C21,
pas avant) : `geoloc_flotte.csv` et le flux SSE portent tous deux
`vehicule_id`/`lat`/`lon` — géolocalisation de la flotte, déjà signalée
comme donnée sensible dans
[`architecture_cible.md` §3](architecture_cible.md) (« purge automatisée
au-delà d'un horizon défini, ex. 90 jours »). `rfid_scans.json` et
`camera_comptage.csv`, en revanche, ne portent aucun identifiant
personnel (palette, zone, comptage agrégé) — pas de donnée personnelle a
priori sur ces deux flux, à confirmer formellement dans le registre RGPD
de C21.

---

## 3. Conséquence sur la création des issues du milestone M3

Les 4 issues du milestone M3 (C18 à C21) sont créées dans cet ordre,
même numérotation croissante que l'ordre de traitement — contrairement
au Bloc 3 où l'ordre de traitement (#48 avant #47) ne suivait pas l'ordre
de création. Le [plan de développement](../plan_de_developpement.md)
référence ce document, sur le même principe que pour les Blocs 2 et 3.
