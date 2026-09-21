"""Extraction des données FluxPro depuis la base de staging PostgreSQL (C8).

Couvre la source « base de données » attendue par le référentiel (voir
`docs/architecture/topographie_donnees.md` section 2). La base de
staging est déjà peuplée par `scripts/init_staging_db.sh` (issue #7) ;
ce module se contente de l'interroger.

`fetch_table()` n'utilise que des primitives SQL standard (DB-API 2.0:
`cursor()`, `.execute()`, `.description`, `.fetchall()`), ce qui la rend
testable avec n'importe quelle connexion compatible (psycopg2 en
production, sqlite3 dans les tests unitaires) sans dépendre d'une vraie
base PostgreSQL.
"""
from typing import Any

import psycopg2

from datacore.config import STAGING_DB_DSN

FLUXPRO_TABLES = (
    "entrepots",
    "clients",
    "produits",
    "commandes",
    "lignes_commande",
    "expeditions",
    "stocks",
)


def connect(dsn: str = STAGING_DB_DSN):
    """Ouvre une connexion à la base de staging PostgreSQL.

    Args:
        dsn: chaîne de connexion PostgreSQL (surclassable pour les tests).

    Returns:
        Une connexion psycopg2 ouverte.
    """
    return psycopg2.connect(dsn)


def fetch_table(conn, table_name: str) -> list[dict[str, Any]]:
    """Extrait l'intégralité d'une table FluxPro sous forme de dictionnaires.

    Args:
        conn: connexion DB-API ouverte (psycopg2 en production, sqlite3
            accepté en test : seules des primitives SQL standard sont
            utilisées).
        table_name: nom de la table à extraire ; doit figurer dans
            `FLUXPRO_TABLES` (liste blanche, évite toute injection SQL
            via le nom de table, qui ne peut pas être paramétré comme une
            valeur en SQL standard).

    Returns:
        La liste des lignes de la table, une par dict colonne -> valeur.

    Raises:
        ValueError: si `table_name` ne fait pas partie des tables FluxPro
            connues.
    """
    if table_name not in FLUXPRO_TABLES:
        raise ValueError(f"Table FluxPro inconnue : {table_name!r}")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
