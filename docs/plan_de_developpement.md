# Plan de développement — DATA CORE

## Contexte
Programme fictif Omega Logistics (3PL), formation Simplon Data Engineer.
Cahier des charges complet : voir section "Référence" plus bas.
Pack technique source : `datacore-dataset` (copié dans `data/raw/`, jamais versionné).

## Découpage en 4 blocs

| Milestone GitHub | Bloc | Compétences | Épreuves |
|---|---|---|---|
| M0 — Cadrage & Setup | Bloc 1 | C1-C7 | E1, E2, E3 |
| M1 — Collecte & Stockage | Bloc 2 | C8-C12 | E4 |
| M2 — Entrepôt OMEGA BI | Bloc 3 | C13-C17 | E5, E6 |
| M3 — Data Lake OMEGA LAKE | Bloc 4 | C18-C21 | E7 |
| M4 — Rapport LaTeX | Transverse | — | — |
| M5 — Présentation orale | Transverse | — | — |

## Convention de branches

- `main` — protégée, releases uniquement
- `dev` — intégration continue, base de toutes les branches de travail
- `feat-<number>-<name>` — une branche par issue GitHub, créée depuis `dev`
  - `<number>` = numéro de l'issue GitHub
  - `<name>` = slug court en kebab-case décrivant la tâche
  - Exemples : `feat-2-etude-faisabilite`, `feat-7-docker-compose`

Toute PR de `feat-*` cible `dev`, jamais `main` directement.
`dev` → `main` uniquement lors d'une release/jalon validé.

## Arborescence de référence
Voir architecture complète discutée avec Claude Web (conversation du 24/08/2026) :
`src/datacore/{ingestion,processing,storage,api,governance,config}`,
`docs/{architecture,latex,presentation}`, `tests/{unit,integration,playwright}`, `infra/`.

## État d'avancement
- [x] Init repo, arborescence, .gitignore, README (#1)
- [x] Étude de faisabilité C1 (#2)
- [x] Topographie des données C2 (#3)
- [x] Architecture AS IS/TO BE C3 (#4)
- [x] Feuille de route C5 (#6)
- [x] Docker-compose (#7)
- [x] CI lint + tests (#8)
- [x] Veille technique et réglementaire C4 (#18)
- [x] Supervision — rituels et budget C6 (#19)
- [x] Plan de communication et lancement C7 (#20)

**M0 clos le 25/08/2026** — voir `docs/comptes_rendus/M0.md` pour le
compte rendu de fin de milestone (livrables, compétences couvertes,
décisions, points ouverts pour M1).

## Règles pour Claude Code
- Ne jamais committer `data/raw/*` (voir `.gitignore`).
- Une branche par issue, nommée selon la convention ci-dessus.
- PR obligatoire vers `dev`, jamais de push direct sur `main` ou `dev`.
- Chaque livrable Markdown/LaTeX doit citer la compétence RNCP couverte (ex. "C1", "C8").

## Référence
Cahier des charges complet : `docs/reference/Cahier_des_charges_DATA_CORE.docx`

## Mise à jour du Kanban
Le champ Status du Project #3 "DATA CORE" compte 6 statuts (étendu le
24/08/2026, IDs des options en mémoire Claude Code) :
`Backlog` → `À faire (sprint)` → `En cours` → `En revue (PR)` → `Bloqué` → `Terminé`.

Cycle de vie type d'une issue :
1. À la prise en charge : assigner l'issue à `alaugier`
   (`gh issue edit <n> --add-assignee alaugier`) et passer son statut à
   `En cours`.
2. À l'ouverture de la PR : passer le statut à `En revue (PR)` (optionnel
   si la PR est mergée immédiatement après review).
3. Après merge de la PR :
   - Fermer l'issue (`gh issue close <n>`) si non fait automatiquement.
   - Passer le statut à `Terminé` via `gh project item-edit`.
   - Cocher la case correspondante dans la section "État d'avancement"
     ci-dessus (dans la même PR que le livrable).
4. Si le travail est stoppé par une dépendance externe, passer le statut
   à `Bloqué` plutôt que de le laisser en `En cours`.

## Compte rendu de fin de milestone
À la fermeture du dernier issue d'un milestone, créer/compléter
docs/comptes_rendus/<milestone>.md avec :
- Liste des livrables produits (chemins de fichiers)
- Compétences couvertes (Cx) et preuves associées
- Décisions techniques et justifications
- Écarts par rapport au cahier des charges (le cas échéant)
- Points ouverts / risques pour le milestone suivant
Commiter ce fichier dans la même PR que la dernière issue du milestone.
