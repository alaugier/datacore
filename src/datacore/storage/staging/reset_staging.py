#!/usr/bin/env python3
"""Vide les tables de la base de staging gérées par Alembic (C11), pour
rejouer le pipeline depuis zéro.

Portée volontairement limitée aux tables décrites dans `models.py`
(transporteurs, tournees, livraisons, commandes_clients,
lignes_commande_clients) -- celles que `load_staging.py` écrit à
chaque exécution, pas idempotent par conception (import one-shot, voir
son docstring). Ne touche JAMAIS aux tables FluxPro (clients, produits,
commandes, entrepots, expeditions, lignes_commande, stocks) ni à
`historique_expeditions` : données "données" chargées une seule fois
par `scripts/init_staging_db.sh` / `scripts/load_historique.sh`, pas
par le pipeline -- les tronquer casserait silencieusement C8 (une
requête SELECT sur une table vide ne lève pas d'exception, elle
retourne juste 0 ligne).

Utilise `metadata.tables` (`models.py`) plutôt qu'une liste de noms en
dur : si une table Alembic est ajoutée plus tard, ce script reste
correct sans modification à faire ici.

Usage :
    python3 -m datacore.storage.staging.reset_staging
"""
import psycopg2

from datacore.config import STAGING_DB_DSN
from datacore.storage.staging.models import metadata


def main() -> None:
    tables = ", ".join(metadata.tables.keys())
    conn = psycopg2.connect(STAGING_DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE")
        conn.commit()
        print(f"Tables réinitialisées : {tables}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
