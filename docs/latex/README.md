# Rapport LaTeX — DATA CORE

Rapport professionnel consolidé (Blocs 1-4, C1-C21, + jalon transverse
M4). Structure et séquencement décidés avant rédaction : voir
[`docs/architecture/sequencement_m5.md`](../architecture/sequencement_m5.md).

## Compiler

```bash
cd docs/latex
pdflatex -interaction=nonstopmode rapport.tex
pdflatex -interaction=nonstopmode rapport.tex  # deuxième passe : résout le sommaire et les renvois internes
```

Nécessite une distribution LaTeX avec `babel`, `hyperref`, `listings`,
`booktabs`, `fancyhdr`, `titlesec` (présentes dans une installation
`texlive-full` standard).

## Structure

- `rapport.tex` — document maître.
- `chapitres/00` à `07` — un fichier par chapitre (voir le plan dans
  `sequencement_m5.md` §2).
- `annexes/` — matrice chapitre ↔ compétence ↔ épreuve ↔ document source.
- `figures/` — réservé, pas encore utilisé à ce stade (chapitres 01-05).

## État d'avancement

- [x] Chapitres 01-05 (issue #90) — synthèse des Blocs 1-4 et du jalon M4.
- [ ] Chapitre 06, synthèse transverse (issue #91).
- [ ] Chapitres 00/07 + annexe (issue #92).
