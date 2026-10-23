# Trame de la soutenance — DATA CORE

Présentation [Slidev](https://sli.dev) (Markdown) de la soutenance
orale de certification. Structure et minutage décidés avant rédaction :
voir
[`docs/architecture/sequencement_m6.md`](../docs/architecture/sequencement_m6.md)
§1.2-2 (issue #97).

50 slides, calibrées sur le déroulé d'épreuve E1-E7 de la certification
(~90-100 minutes au total, hypothèse de travail à confirmer avec le
formateur). Contenu dérivé du rapport (`docs/latex/rapport.pdf`) et des
diagrammes déjà exportés (`docs/architecture/images/`, copiés ici dans
`public/images/`, pas redessinés).

## Lancer

```bash
cd slides
npm install
npm run dev       # serveur de présentation local, http://localhost:3030
```

## Exporter

```bash
npm install -D playwright-chromium   # une seule fois, nécessaire à l'export
npx playwright install chromium
npm run export -- --output soutenance.pdf
```

`--per-slide --wait 800` (déjà dans le script `export`) : nécessaire
pour que les grandes images (ex. le diagramme C8) aient le temps de se
charger avant la capture -- sans ces options, l'export standard de
Slidev peut produire une page vide pour un slide dont l'image n'a pas
fini de se décoder (flaky, propre à l'export PDF, jamais reproduit dans
le rendu live `npm run dev`).

## Structure

- `slides.md` — document source unique (frontmatter + une section par
  `---`), thème `seriph`.
- `global-bottom.vue` — pagination (bas-droite, absente sur la page de
  garde), chargée automatiquement sur chaque slide par Slidev.
- `public/images/` — copies des diagrammes Mermaid déjà exportés en PNG
  (aucun schéma redessiné pour cette présentation).
- `public/logos/` — logos de services (PostgreSQL, Docker, Grafana,
  DuckDB, MinIO, GitHub, FastAPI), extraits du paquet
  [simple-icons](https://github.com/simple-icons/simple-icons) (CC0),
  copiés tels quels -- pas une dépendance npm du projet.
- `public/illustrations/` — illustrations décoratives, extraites du
  paquet [undraw-svg](https://www.npmjs.com/package/undraw-svg) (MIT),
  copiées telles quelles -- pas une dépendance npm du projet.

`node_modules/`, les exports (`*.pdf`, `*.pptx`) et le build (`dist/`)
ne sont jamais versionnés (`.gitignore` racine).
