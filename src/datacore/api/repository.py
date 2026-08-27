"""Accès aux données consolidées pour l'Omega Data API (C12).

Fonctions d'accès SQL directes (psycopg2), testées avec des doubles de
connexion (voir `tests/unit/test_api_repository.py`) — la correction du
SQL lui-même est vérifiée par un test de bout en bout contre une vraie
base (Docker Compose), suivant le même principe que
`datacore.storage.staging.load_staging`.
"""
from typing import Any


def _rows_as_dicts(cur: Any) -> list[dict[str, Any]]:
    """Convertit le résultat courant d'un curseur en liste de dicts colonne -> valeur."""
    columns = [d[0] for d in cur.description]
    return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def list_commandes_clients(
    conn: Any, client: str | None = None, limit: int = 50, offset: int = 0
) -> list[dict[str, Any]]:
    """Liste les en-têtes de commandes clients consolidées (C10/C11), filtrables par client.

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        client: si fourni, restreint aux commandes de ce client.
        limit: nombre maximum de lignes renvoyées.
        offset: décalage pour la pagination.

    Returns:
        La liste des en-têtes de commandes correspondants.
    """
    cur = conn.cursor()
    if client:
        cur.execute(
            """
            SELECT id, client, commande_id, date_commande, entrepot
            FROM commandes_clients
            WHERE client = %s
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            (client, limit, offset),
        )
    else:
        cur.execute(
            """
            SELECT id, client, commande_id, date_commande, entrepot
            FROM commandes_clients
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
    return _rows_as_dicts(cur)


def get_commande_client(conn: Any, commande_client_id: int) -> dict[str, Any] | None:
    """Récupère un en-tête de commande client par son id.

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        commande_client_id: identifiant de la commande.

    Returns:
        Le dict de la commande, ou None si elle n'existe pas.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT id, client, commande_id, date_commande, entrepot "
        "FROM commandes_clients WHERE id = %s",
        (commande_client_id,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    columns = [d[0] for d in cur.description]
    return dict(zip(columns, row, strict=True))


def list_lignes_commande_client(conn: Any, commande_client_id: int) -> list[dict[str, Any]]:
    """Liste les lignes d'une commande client, enrichies du référentiel produit FluxPro.

    `libelle_produit`, `poids_kg` et `temperature_dirigee` sont obtenus
    par jointure sur `produits.sku` plutôt que stockés en double (voir
    `docs/architecture/modelisation_merise.md` §3.4).

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        commande_client_id: identifiant de la commande (en-tête).

    Returns:
        La liste des lignes de la commande.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT lcc.id, lcc.sku, p.libelle AS libelle_produit, lcc.quantite,
               p.poids_kg, p.temperature_dirigee
        FROM lignes_commande_clients lcc
        JOIN produits p ON p.sku = lcc.sku
        WHERE lcc.commande_client_id = %s
        ORDER BY lcc.id
        """,
        (commande_client_id,),
    )
    return _rows_as_dicts(cur)


def list_livraisons(
    conn: Any, statut: str | None = None, limit: int = 50, offset: int = 0
) -> list[dict[str, Any]]:
    """Liste les livraisons TransFlow, avec statut dérivé, filtrables par statut.

    Interroge la vue `livraisons_avec_statut` (C11) plutôt que la table
    `livraisons` : `statut` n'y est pas stocké, il y est recalculé
    depuis `heure_reelle` (voir `modelisation_merise.md` §3.3).

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        statut: si fourni, restreint aux livraisons de ce statut
            (`"Livree"` ou `"En cours"`).
        limit: nombre maximum de lignes renvoyées.
        offset: décalage pour la pagination.

    Returns:
        La liste des livraisons correspondantes.
    """
    cur = conn.cursor()
    if statut:
        cur.execute(
            """
            SELECT id, tournee_id, tracking_number, heure_estimee, heure_reelle, statut
            FROM livraisons_avec_statut
            WHERE statut = %s
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            (statut, limit, offset),
        )
    else:
        cur.execute(
            """
            SELECT id, tournee_id, tracking_number, heure_estimee, heure_reelle, statut
            FROM livraisons_avec_statut
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
    return _rows_as_dicts(cur)


def taux_service_par_client(conn: Any, client: str | None = None) -> list[dict[str, Any]]:
    """Calcule le taux de service (livraisons à l'heure) par client, sur FluxPro.

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        client: si fourni, restreint le calcul à ce client.

    Returns:
        Une ligne par client : nombre d'expéditions et taux de service (%).
    """
    cur = conn.cursor()
    base_sql = """
        SELECT
            c.nom AS client,
            count(*) AS nb_expeditions,
            round(
                100.0 * sum(
                    CASE WHEN exp.date_livraison_reelle <= exp.date_livraison_prevue
                    THEN 1 ELSE 0 END
                ) / count(*),
                1
            ) AS taux_service_pct
        FROM expeditions exp
        JOIN commandes cmd ON cmd.id = exp.commande_id
        JOIN clients c ON c.id = cmd.client_id
        WHERE exp.date_livraison_reelle IS NOT NULL
    """
    if client:
        cur.execute(base_sql + " AND c.nom = %s GROUP BY c.nom ORDER BY c.nom", (client,))
    else:
        cur.execute(base_sql + " GROUP BY c.nom ORDER BY c.nom")
    return _rows_as_dicts(cur)
