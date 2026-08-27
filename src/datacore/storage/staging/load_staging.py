#!/usr/bin/env python3
"""Import documenté des données consolidées dans la base de travail (C11).

Charge, dans les tables gérées par Alembic
(`src/datacore/storage/staging/models.py`), les résultats des zones
d'atterrissage écrites par C8 (TransFlow) et C10 (fichiers clients
nettoyés) :

- `data/interim/transflow_transporteurs.json` -> table `transporteurs`
- `data/interim/transflow_tournees.json`      -> table `tournees`
- `data/interim/transflow_livraisons.json`    -> table `livraisons`
  (le statut n'est plus stocké : voir la vue `livraisons_avec_statut`)
- `data/interim/clients_consolidated.json`    -> tables `commandes_clients`
  (en-tête) et `lignes_commande_clients` (une ligne par produit).
  `libelle_produit`/`poids_kg`/`chaine_froid_requise` ne sont pas
  importés : dérivables de `produits` (FluxPro) via `sku` (vérifié
  empiriquement sans écart, voir `docs/architecture/modelisation_merise.md`).

Prérequis : `alembic upgrade head` appliqué, et C8
(`python3 -m datacore.ingestion.run_extraction`) puis C10
(`python3 -m datacore.processing.run_cleaning`) déjà exécutés.

Lancement :
    python3 -m datacore.storage.staging.load_staging

L'import est transactionnel : un échec sur n'importe quelle étape
annule (`ROLLBACK`) l'ensemble, aucune table n'est laissée partiellement
peuplée.
"""
from typing import Any

import psycopg2

from datacore.ingestion.config import INTERIM_DIR, STAGING_DB_DSN
from datacore.ingestion.landing import read_records


def load_transporteurs(conn, records: list[dict[str, Any]]) -> int:
    """Insère les transporteurs, en conservant leurs id d'origine (TransFlow).

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        records: enregistrements bruts issus de
            `data/interim/transflow_transporteurs.json`.

    Returns:
        Le nombre de lignes insérées.
    """
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO transporteurs (id, nom, contact) VALUES (%(id)s, %(nom)s, %(contact)s)",
        records,
    )
    if records:
        cur.execute("SELECT setval('transporteurs_id_seq', (SELECT max(id) FROM transporteurs))")
    return len(records)


def load_tournees(conn, records: list[dict[str, Any]]) -> int:
    """Insère les tournées, en conservant leurs id d'origine (TransFlow).

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        records: enregistrements bruts issus de
            `data/interim/transflow_tournees.json`.

    Returns:
        Le nombre de lignes insérées.
    """
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO tournees (id, transporteur_id, date, vehicule_id, chauffeur)
        VALUES (%(id)s, %(transporteur_id)s, %(date)s, %(vehicule_id)s, %(chauffeur)s)
        """,
        records,
    )
    if records:
        cur.execute("SELECT setval('tournees_id_seq', (SELECT max(id) FROM tournees))")
    return len(records)


def load_livraisons(conn, records: list[dict[str, Any]]) -> int:
    """Insère les livraisons, en conservant leur id d'origine (TransFlow).

    Le `statut` n'est pas inséré : la table ne le stocke plus (voir la
    vue `livraisons_avec_statut`, qui le recalcule depuis `heure_reelle`).

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        records: enregistrements bruts issus de
            `data/interim/transflow_livraisons.json`.

    Returns:
        Le nombre de lignes insérées.
    """
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO livraisons
            (id, tournee_id, tracking_number, adresse_livraison, heure_estimee, heure_reelle)
        VALUES
            (%(id)s, %(tournee_id)s, %(tracking_number)s, %(adresse_livraison)s,
             %(heure_estimee)s, %(heure_reelle)s)
        """,
        records,
    )
    if records:
        cur.execute("SELECT setval('livraisons_id_seq', (SELECT max(id) FROM livraisons))")
    return len(records)


def load_commandes_clients(conn, records: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    """Insère les en-têtes de commandes clients, dédupliqués sur (client, commande_id).

    `records` contient une ligne par produit commandé (sortie de C10) ;
    plusieurs lignes partagent donc le même (client, commande_id). Un
    seul en-tête est inséré par commande (date_commande et entrepot sont
    constants au sein d'une même commande, vérifié empiriquement — voir
    `docs/architecture/modelisation_merise.md` §7.1).

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        records: enregistrements consolidés issus de
            `data/interim/clients_consolidated.json` (sortie de C10).

    Returns:
        dict associant (client, commande_id) -> id généré en base,
        nécessaire pour rattacher les lignes correspondantes
        (`load_lignes_commande_clients`).
    """
    headers: dict[tuple[str, str], dict[str, Any]] = {}
    for r in records:
        key = (r["client"], r["commande_id"])
        headers.setdefault(
            key,
            {
                "client": r["client"],
                "commande_id": r["commande_id"],
                "date_commande": r["date_commande"],
                "entrepot": r["entrepot"],
            },
        )

    cur = conn.cursor()
    header_ids: dict[tuple[str, str], int] = {}
    for key, header in headers.items():
        cur.execute(
            """
            INSERT INTO commandes_clients (client, commande_id, date_commande, entrepot)
            VALUES (%(client)s, %(commande_id)s, %(date_commande)s, %(entrepot)s)
            RETURNING id
            """,
            header,
        )
        header_ids[key] = cur.fetchone()[0]
    return header_ids


def load_lignes_commande_clients(
    conn, records: list[dict[str, Any]], header_ids: dict[tuple[str, str], int]
) -> int:
    """Insère les lignes de commande client, rattachées à leur en-tête.

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        records: enregistrements consolidés issus de
            `data/interim/clients_consolidated.json` (sortie de C10).
        header_ids: correspondance (client, commande_id) -> id d'en-tête,
            produite par `load_commandes_clients`.

    Returns:
        Le nombre de lignes insérées.
    """
    cur = conn.cursor()
    rows = [
        {
            "commande_client_id": header_ids[(r["client"], r["commande_id"])],
            "sku": r["sku"],
            "quantite": r["quantite"],
        }
        for r in records
    ]
    cur.executemany(
        """
        INSERT INTO lignes_commande_clients (commande_client_id, sku, quantite)
        VALUES (%(commande_client_id)s, %(sku)s, %(quantite)s)
        """,
        rows,
    )
    return len(rows)


def main() -> None:
    """Charge toutes les tables depuis la zone d'atterrissage, dans une transaction unique.

    En cas d'erreur sur n'importe quelle étape, annule l'ensemble
    (`ROLLBACK`) plutôt que de laisser une base partiellement peuplée.
    """
    conn = psycopg2.connect(STAGING_DB_DSN)
    try:
        n_transporteurs = load_transporteurs(
            conn, read_records(INTERIM_DIR / "transflow_transporteurs.json")
        )
        n_tournees = load_tournees(conn, read_records(INTERIM_DIR / "transflow_tournees.json"))
        n_livraisons = load_livraisons(
            conn, read_records(INTERIM_DIR / "transflow_livraisons.json")
        )

        commandes_clients_records = read_records(INTERIM_DIR / "clients_consolidated.json")
        header_ids = load_commandes_clients(conn, commandes_clients_records)
        n_lignes = load_lignes_commande_clients(conn, commandes_clients_records, header_ids)

        conn.commit()
        print(
            f"transporteurs: {n_transporteurs}, tournees: {n_tournees}, "
            f"livraisons: {n_livraisons}, commandes_clients: {len(header_ids)}, "
            f"lignes_commande_clients: {n_lignes}"
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
