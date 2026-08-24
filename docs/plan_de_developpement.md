# Plan de développement — DATA CORE

## Contexte
Programme fictif Omega Logistics (3PL), formation Simplon Data Engineer.
Cahier des charges complet : voir `Cahier_des_charges_DATA_CORE.docx` (fourni hors repo, demander à Alexandre si besoin de référence).
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
- [ ] Étude de faisabilité C1 (#2)
- [ ] Topographie des données C2 (#3)
- [ ] Architecture AS IS/TO BE C3 (#4)
- [ ] Feuille de route C5 (#6)
- [ ] Docker-compose (#7)
- [ ] CI lint + tests (#8)

## Règles pour Claude Code
- Ne jamais committer `data/raw/*` (voir `.gitignore`).
- Une branche par issue, nommée selon la convention ci-dessus.
- PR obligatoire vers `dev`, jamais de push direct sur `main` ou `dev`.
- Chaque livrable Markdown/LaTeX doit citer la compétence RNCP couverte (ex. "C1", "C8").
