"""Écriture/lecture des données extraites dans la zone d'atterrissage intermédiaire.

Avant que la base de travail consolidée (C11, modélisation MERISE)
n'existe, les scripts d'extraction (C8) atterrissent dans des fichiers
JSON sous `data/interim/` (non versionnés, voir `.gitignore`) : un
fichier par source, servant d'entrée aux étapes de nettoyage (C10) et
de modélisation (C11).
"""
import datetime
import decimal
import json
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    """Convertit les types non JSON-natifs renvoyés par psycopg2 (C8/FluxPro).

    Args:
        value: objet que `json.dump` ne sait pas sérialiser nativement
            (ex. `decimal.Decimal` pour les colonnes NUMERIC/DECIMAL,
            `datetime.date`/`datetime.datetime` pour les colonnes DATE).

    Returns:
        Une représentation JSON-compatible (`float` pour un `Decimal`,
        chaîne ISO 8601 pour une date).

    Raises:
        TypeError: si le type n'est pas géré, propagée par `json.dump`.
    """
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    raise TypeError(f"Objet non sérialisable en JSON : {value!r} ({type(value).__name__})")


def write_records(records: list[dict[str, Any]], path: Path) -> Path:
    """Écrit une liste d'enregistrements en JSON dans la zone d'atterrissage.

    Args:
        records: liste de dictionnaires à sérialiser.
        path: chemin du fichier de sortie ; le dossier parent est créé
            si besoin.

    Returns:
        Le chemin du fichier écrit (identique à `path`).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=_json_default)
    return path


def read_records(path: Path) -> list[dict[str, Any]]:
    """Relit une liste d'enregistrements précédemment écrite par `write_records`.

    Args:
        path: chemin du fichier JSON à lire.

    Returns:
        La liste de dictionnaires désérialisée.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)
