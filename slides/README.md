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

## Structure

- `slides.md` — document source unique (frontmatter + une section par
  `---`), thème `seriph`.
- `public/images/` — copies des diagrammes Mermaid déjà exportés en PNG
  (aucun schéma redessiné pour cette présentation).

`node_modules/`, les exports (`*.pdf`, `*.pptx`) et le build (`dist/`)
ne sont jamais versionnés (`.gitignore` racine).
