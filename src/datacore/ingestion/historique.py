"""Lecture du fichier d'historique volumineux des expéditions (C8).

Couvre la source « système big data » attendue par le référentiel (voir
`docs/architecture/topographie_donnees.md` section 3.4) : 25 000 lignes,
période 2022-2026.
"""
import csv
from pathlib import Path
from typing import Any

from datacore.ingestion.config import HISTORIQUE_PATH


def read_historique(path: Path | None = None) -> list[dict[str, Any]]:
    """Lit l'historique d'expéditions en liste de dictionnaires.

    Args:
        path: chemin du fichier CSV (par défaut `data/raw/historique/...`).

    Returns:
        La liste des lignes de l'historique, une par dict colonne -> valeur.
    """
    with open(path or HISTORIQUE_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=","))
