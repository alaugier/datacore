"""Journalisation des opérations de maintenance de l'entrepôt OMEGA BI (C16).

Chaque exécution d'une opération de maintenance (chargement ETL,
sauvegarde) est enregistrée dans `gouvernance.journal_operations` —
début, fin, statut, résumé ou message d'erreur. Aucune donnée métier ou
personnelle n'y transite, uniquement des métadonnées d'exécution (voir
`docs/architecture/registre_rgpd_entrepot.md`).
"""
import contextlib
import datetime
from collections.abc import Iterator
from typing import Any

import psycopg2

from datacore.config import OMEGA_BI_DB_DSN


@contextlib.contextmanager
def journaliser(operation: str, dsn: str = OMEGA_BI_DB_DSN) -> Iterator[dict[str, Any]]:
    """Journalise le déroulement d'une opération dans `gouvernance.journal_operations`.

    Enregistre une ligne au début (`statut = en_cours`), puis la met à
    jour à la sortie du bloc — `succes` avec `details`, ou `echec` avec
    le message d'erreur si le bloc lève une exception (qui est ensuite
    relancée : ce gestionnaire journalise, il n'avale pas les erreurs).

    Args:
        operation: nom court de l'opération journalisée (ex.
            `"load_warehouse"`, `"backup_complet"`).
        dsn: chaîne de connexion vers l'entrepôt.

    Yields:
        Un dict mutable : y écrire la clé `"details"` avant la fin du
        bloc pour que ce résumé soit journalisé en cas de succès.

    Example:
        >>> with journaliser("load_warehouse") as contexte:
        ...     n = faire_le_travail()
        ...     contexte["details"] = f"{n} lignes chargées"
    """
    conn = psycopg2.connect(dsn)
    contexte: dict[str, Any] = {"details": None}
    demarre_le = datetime.datetime.now()

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO gouvernance.journal_operations (operation, demarre_le, statut) "
            "VALUES (%s, %s, 'en_cours') RETURNING id",
            (operation, demarre_le),
        )
        row = cur.fetchone()
        assert row is not None  # INSERT ... RETURNING id renvoie toujours une ligne
        op_id = row[0]
        conn.commit()

    try:
        yield contexte
    except Exception as exc:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE gouvernance.journal_operations
                SET termine_le = %s, statut = 'echec', erreur = %s
                WHERE id = %s
                """,
                (datetime.datetime.now(), str(exc), op_id),
            )
            conn.commit()
        raise
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE gouvernance.journal_operations
                SET termine_le = %s, statut = 'succes', details = %s
                WHERE id = %s
                """,
                (datetime.datetime.now(), contexte.get("details"), op_id),
            )
            conn.commit()
    finally:
        conn.close()
