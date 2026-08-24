# DATA CORE — Omega Logistics

Programme de refonte de l'infrastructure data (formation Simplon).
4 blocs de compétences : cadrage (M0-M0), collecte/stockage (M1),
entrepôt OMEGA BI (M2), data lake OMEGA LAKE (M3).

## Structure
Voir `docs/architecture/` pour l'AS IS/TO BE et le détail des modules `src/datacore/`.

## Setup local
\`\`\`bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd api-mock && python3 app.py   # API mock TransFlow sur :5050
\`\`\`

## Données
`data/raw/` contient le pack pédagogique fourni (non versionné, voir .gitignore).
