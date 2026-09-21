"""Exporte chaque diagramme Mermaid des documents d'architecture en PNG.

Rend chaque bloc ```mermaid``` de `docs/architecture/*.md` via mermaid-cli
(`mmdc`, exécuté par `npx` — aucune installation globale requise) dans
`docs/architecture/images/`. Les blocs Mermaid dans les documents restent
la source de vérité éditable ; les PNG sont des exports dérivés destinés
au rapport LaTeX (milestone M4), à régénérer après toute modification
d'un diagramme.

Usage : python3 scripts/export_mermaid_diagrams.py
"""
import re
import subprocess
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs" / "architecture"
OUT = DOCS / "images"

# (fichier source, slugs de sortie dans l'ordre d'apparition des blocs).
TARGETS: dict[str, list[str]] = {
    "modelisation_omega_bi.md": ["modelisation_omega_bi_mcd"],
    "feuille_de_route.md": ["feuille_de_route_gantt", "feuille_de_route_pert"],
    "diagrammes_techniques.md": [
        "diagrammes_techniques_ingestion_c8",
        "diagrammes_techniques_api_modules",
        "diagrammes_techniques_api_sequence_autorisation",
    ],
    "modelisation_merise.md": ["modelisation_merise_mcd"],
}

MERMAID_BLOCK = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)


def export_diagrams() -> None:
    """Extrait et rend chaque bloc Mermaid référencé dans TARGETS.

    Args: aucun.
    Lève AssertionError si le nombre de blocs Mermaid trouvés dans un
    fichier ne correspond pas aux slugs déclarés (signale un diagramme
    ajouté/retiré sans mise à jour de TARGETS).
    """
    OUT.mkdir(exist_ok=True)
    for filename, slugs in TARGETS.items():
        path = DOCS / filename
        blocks = MERMAID_BLOCK.findall(path.read_text())
        assert len(blocks) == len(slugs), (
            f"{filename}: {len(blocks)} blocs Mermaid trouvés, "
            f"{len(slugs)} attendus dans TARGETS — mettre à jour ce script."
        )
        for block, slug in zip(blocks, slugs):
            mmd_path = OUT / f"{slug}.mmd"
            png_path = OUT / f"{slug}.png"
            mmd_path.write_text(block + "\n")
            print(f"Rendu {filename} -> images/{slug}.png")
            subprocess.run(
                [
                    "npx", "--yes", "@mermaid-js/mermaid-cli",
                    "-i", str(mmd_path),
                    "-o", str(png_path),
                    "-b", "white",
                    "-w", "1600",
                    "-s", "2",
                ],
                check=True,
                cwd=str(OUT),
            )
            mmd_path.unlink()


if __name__ == "__main__":
    export_diagrams()
