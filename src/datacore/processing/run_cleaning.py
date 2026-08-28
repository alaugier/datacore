#!/usr/bin/env python3
"""Nettoie et agrège les fichiers clients extraits par C8 (C10).

Lit les trois fichiers clients bruts depuis la zone d'atterrissage
intermédiaire déposée par `datacore.ingestion.run_extraction`
(`data/interim/clients_*.json`), produit le jeu de données consolidé
unique, et l'écrit dans `data/interim/clients_consolidated.json`.

Lancement :
    python3 -m datacore.processing.run_cleaning

Prérequis : avoir lancé au préalable
`python3 -m datacore.ingestion.run_extraction` (C8).
"""
import json

from datacore.config import INTERIM_DIR
from datacore.ingestion.landing import read_records, write_records
from datacore.processing.clients_cleaning import clean_and_aggregate


def main() -> None:
    """Nettoie les trois fichiers clients et écrit le jeu de données consolidé."""
    norddrive_raw = read_records(INTERIM_DIR / "clients_norddrive.json")
    freshmarket_raw = read_records(INTERIM_DIR / "clients_freshmarket.json")
    mediotex_raw = read_records(INTERIM_DIR / "clients_mediotex.json")

    result = clean_and_aggregate(norddrive_raw, freshmarket_raw, mediotex_raw)

    write_records(result["records"], INTERIM_DIR / "clients_consolidated.json")
    print(json.dumps(result["rapport"], indent=2, ensure_ascii=False))
    print(f"{len(result['records'])} lignes consolidées écrites dans {INTERIM_DIR}")


if __name__ == "__main__":
    main()
