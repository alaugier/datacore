"""Connexion à la base de staging, une par requête, pour l'Omega Data API (C12)."""
from collections.abc import Iterator

import psycopg2
import psycopg2.extensions

from datacore.config import STAGING_DB_DSN


def get_db() -> Iterator[psycopg2.extensions.connection]:
    """Fournit une connexion à la base de staging, fermée à la fin de la requête.

    Dépendance FastAPI (générateur) : la connexion est ouverte avant
    l'exécution de la route, puis systématiquement fermée après (y
    compris en cas d'exception dans la route).

    Yields:
        Une connexion psycopg2 ouverte sur la base de staging.
    """
    conn = psycopg2.connect(STAGING_DB_DSN)
    try:
        yield conn
    finally:
        conn.close()
