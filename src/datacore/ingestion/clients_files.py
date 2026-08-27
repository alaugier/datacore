"""Lecture brute des fichiers de commandes clients (NordDrive, FreshMarket, MedioTex) (C8).

Couvre la source « fichier de données » attendue par le référentiel (voir
`docs/architecture/topographie_donnees.md` section 3.3). Chaque client
utilise un format différent (délimiteur, colonnes) : ce module se
contente d'une lecture fidèle, sans nettoyage — le dédoublonnage et
l'homogénéisation des formats sont le rôle de C10.
"""
import csv
from pathlib import Path
from typing import Any

from datacore.ingestion.config import CLIENTS_FILES_DIR


def _read_csv(path: Path, delimiter: str) -> list[dict[str, Any]]:
    """Lit un fichier CSV en liste de dictionnaires, sans transformation.

    Args:
        path: chemin du fichier CSV.
        delimiter: caractère délimiteur de colonnes.

    Returns:
        La liste des lignes, une par dict colonne -> valeur brute.
    """
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def read_norddrive(path: Path | None = None) -> list[dict[str, Any]]:
    """Lit le fichier de commandes NordDrive (délimiteur `;`).

    Args:
        path: chemin du fichier (par défaut celui de `data/raw/`).

    Returns:
        La liste brute des lignes de commandes NordDrive.
    """
    return _read_csv(path or CLIENTS_FILES_DIR / "norddrive_commandes.csv", delimiter=";")


def read_freshmarket(path: Path | None = None) -> list[dict[str, Any]]:
    """Lit le fichier de commandes FreshMarket (délimiteur `,`).

    Args:
        path: chemin du fichier (par défaut celui de `data/raw/`).

    Returns:
        La liste brute des lignes de commandes FreshMarket.
    """
    return _read_csv(path or CLIENTS_FILES_DIR / "freshmarket_commandes.csv", delimiter=",")


def read_mediotex(path: Path | None = None) -> list[dict[str, Any]]:
    """Lit le fichier de commandes MedioTex (délimiteur `,`).

    Args:
        path: chemin du fichier (par défaut celui de `data/raw/`).

    Returns:
        La liste brute des lignes de commandes MedioTex.
    """
    return _read_csv(path or CLIENTS_FILES_DIR / "mediotex_commandes.csv", delimiter=",")


def read_all_clients() -> dict[str, list[dict[str, Any]]]:
    """Lit les trois fichiers clients bruts.

    Returns:
        dict avec les clés "norddrive", "freshmarket", "mediotex", chacune
        associée à la liste brute des lignes du fichier correspondant.
    """
    return {
        "norddrive": read_norddrive(),
        "freshmarket": read_freshmarket(),
        "mediotex": read_mediotex(),
    }
