#!/usr/bin/env python3
"""Import documenté des données consolidées dans la base de travail (C11).

Charge, dans les tables gérées par Alembic
(`src/datacore/storage/staging/models.py`), les résultats des zones
d'atterrissage écrites par C8 (TransFlow) et C10 (fichiers clients
nettoyés) :

- `data/interim/transflow_transporteurs.json` -> table `transporteurs`
- `data/interim/transflow_tournees.json`      -> table `tournees`
- `data/interim/transflow_livraisons.json`    -> table `livraisons`
- `data/interim/clients_consolidated.json`    -> table `commandes_clients`

Prérequis : `alembic upgrade head` appliqué, et C8
(`python3 -m datacore.ingestion.run_extraction`) puis C10
(`python3 -m datacore.processing.run_cleaning`) déjà exécutés.

Lancement :
    python3 -m datacore.storage.staging.load_staging
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
            (id, tournee_id, tracking_number, adresse_livraison, statut,
             heure_estimee, heure_reelle)
        VALUES
            (%(id)s, %(tournee_id)s, %(tracking_number)s, %(adresse_livraison)s, %(statut)s,
             %(heure_estimee)s, %(heure_reelle)s)
        """,
        records,
    )
    if records:
        cur.execute("SELECT setval('livraisons_id_seq', (SELECT max(id) FROM livraisons))")
    return len(records)


def load_commandes_clients(conn, records: list[dict[str, Any]]) -> int:
    """Insère les commandes clients consolidées (id généré par la base).

    Args:
        conn: connexion psycopg2 ouverte sur la base de staging.
        records: enregistrements consolidés issus de
            `data/interim/clients_consolidated.json` (sortie de C10, sans
            identifiant numérique propre : la clé naturelle est le
            triplet client/commande_id/sku).

    Returns:
        Le nombre de lignes insérées.
    """
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO commandes_clients
            (client, commande_id, date_commande, sku, libelle_produit,
             quantite, poids_kg, entrepot, chaine_froid_requise)
        VALUES
            (%(client)s, %(commande_id)s, %(date_commande)s, %(sku)s, %(libelle_produit)s,
             %(quantite)s, %(poids_kg)s, %(entrepot)s, %(chaine_froid_requise)s)
        """,
        records,
    )
    return len(records)


def main() -> None:
    """Charge les quatre tables depuis la zone d'atterrissage et valide la transaction."""
    conn = psycopg2.connect(STAGING_DB_DSN)
    try:
        n_transporteurs = load_transporteurs(
            conn, read_records(INTERIM_DIR / "transflow_transporteurs.json")
        )
        n_tournees = load_tournees(conn, read_records(INTERIM_DIR / "transflow_tournees.json"))
        n_livraisons = load_livraisons(
            conn, read_records(INTERIM_DIR / "transflow_livraisons.json")
        )
        n_commandes_clients = load_commandes_clients(
            conn, read_records(INTERIM_DIR / "clients_consolidated.json")
        )
        conn.commit()
        print(
            f"transporteurs: {n_transporteurs}, tournees: {n_tournees}, "
            f"livraisons: {n_livraisons}, commandes_clients: {n_commandes_clients}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
