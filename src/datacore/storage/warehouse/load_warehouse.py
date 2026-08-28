#!/usr/bin/env python3
"""Pipeline ETL : base de travail (staging) vers l'entrepôt OMEGA BI (C15).

Implémente les règles de transformation « table-relations vers
faits-dimensions » conçues en C13
(`docs/architecture/modelisation_omega_bi.md`) sur le schéma physique
créé en C14. Deux bases Postgres distinctes (`STAGING_DB_DSN` et
`OMEGA_BI_DB_DSN`) : aucune jointure croisée possible côté SQL, toute
transformation se fait en Python entre l'extraction (staging) et le
chargement (entrepôt).

**Rechargement complet, pas incrémental** : chaque exécution vide
d'abord les tables qu'il alimente (`truncate_warehouse`, hors
`dimensions.dim_temps` — dimension générée, chargée séparément par
`load_dim_temps.py`, C14) puis recharge tout depuis staging. Cohérent
avec le rythme batch quotidien/hebdomadaire prévu
(`docs/architecture/architecture_cible.md`, flux F6) et avec l'absence
d'historisation avant C17 (SCD2 sur `Dim_Client`) : un rechargement
complet est plus simple à raisonner qu'une logique d'upsert incrémentale
tant qu'aucune dimension ne conserve d'historique.

**Contrôles qualité** :
- Unicité : `dimensions.dim_categorie.libelle` et le grain de
  `exploitation.fait_stock` sont contraints en base (C14) — une
  violation lève une erreur Postgres explicite plutôt que d'insérer un
  doublon silencieux.
- Rapprochement textuel de l'historique (`client`, `entrepot`,
  `categorie_produit`) : les lignes qui ne correspondent à aucune valeur
  connue sont mises en quarantaine (comptées, non insérées) plutôt que
  rejetées en bloc ou insérées avec une clé fausse — voir
  `load_fait_expedition_historique`.
- Hypothèse « un client = une catégorie de produits » (vérifiée
  empiriquement en C13,
  `notebooks/exploration_donnees_omega_bi.ipynb` §2) : `ValueError`
  explicite si elle s'avérait fausse, plutôt qu'une catégorie choisie
  arbitrairement.

Lancement (après `alembic -c alembic_omega_bi.ini upgrade head` et
`python3 -m datacore.storage.warehouse.load_dim_temps`) :
    python3 -m datacore.storage.warehouse.load_warehouse
"""
import datetime
from typing import Any

import psycopg2
import psycopg2.extras

from datacore.config import OMEGA_BI_DB_DSN, STAGING_DB_DSN

FAIT_EXPEDITION_COLUMNS = """
    client_key, site_key, categorie_key, date_key, transporteur_key,
    tracking_number, source_systeme, poids_kg, delai_livraison_jours,
    cout_transport_eur, statut, livre_a_lheure
"""
FAIT_EXPEDITION_PLACEHOLDERS = """
    %(client_key)s, %(site_key)s, %(categorie_key)s, %(date_key)s, %(transporteur_key)s,
    %(tracking_number)s, %(source_systeme)s, %(poids_kg)s, %(delai_livraison_jours)s,
    %(cout_transport_eur)s, %(statut)s, %(livre_a_lheure)s
"""


def _date_key(d: datetime.date) -> int:
    """Convertit une date en clé YYYYMMDD, le grain de `dimensions.dim_temps`."""
    return int(d.strftime("%Y%m%d"))


def _fetch_dicts(conn: Any, sql: str) -> list[dict[str, Any]]:
    """Exécute une requête en lecture et renvoie les lignes sous forme de dicts.

    Args:
        conn: connexion psycopg2 ouverte (base de staging, en lecture seule ici).
        sql: requête SELECT à exécuter.

    Returns:
        Une liste de dicts colonne -> valeur, une par ligne renvoyée.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return [dict(row) for row in cur.fetchall()]


def _lookup_by_column(conn: Any, table: str, key_column: str, value_column: str) -> dict[Any, int]:
    """Relit une table de l'entrepôt déjà chargée pour construire un dict valeur -> clé.

    Utilisé pour les rapprochements textuels de l'historique (`nom`,
    `ville`) sans dupliquer la logique de dérivation déjà appliquée lors
    du chargement de la dimension.

    Args:
        conn: connexion psycopg2 ouverte sur l'entrepôt.
        table: nom qualifié de la table (ex. `"dimensions.dim_client"`).
        key_column: colonne de clé de substitution à renvoyer.
        value_column: colonne de valeur à utiliser comme clé du dict.

    Returns:
        Un dict `{valeur: clé}`.
    """
    with conn.cursor() as cur:
        cur.execute(f"SELECT {value_column}, {key_column} FROM {table}")  # noqa: S608
        return dict(cur.fetchall())


def truncate_warehouse(warehouse_conn: Any) -> None:
    """Vide les tables alimentées par ce pipeline avant un rechargement complet.

    `dimensions.dim_temps` n'est volontairement pas tronquée (voir
    docstring du module).

    Args:
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.
    """
    with warehouse_conn.cursor() as cur:
        cur.execute("""
            TRUNCATE
                dimensions.dim_client, dimensions.dim_site,
                dimensions.dim_categorie, dimensions.dim_produit,
                dimensions.dim_transporteur,
                exploitation.fait_expedition, exploitation.fait_stock,
                commercial.fait_commande
            CASCADE
        """)


def load_dim_client(staging_conn: Any, warehouse_conn: Any) -> dict[int, int]:
    """Charge `Dim_Client` depuis `staging.clients`.

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.

    Returns:
        Mapping `clients.id` (staging) -> `client_key` (entrepôt).
    """
    rows = _fetch_dicts(staging_conn, "SELECT id, code, nom, secteur FROM clients ORDER BY id")
    mapping: dict[int, int] = {}
    with warehouse_conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                INSERT INTO dimensions.dim_client (client_id, code, nom, secteur)
                VALUES (%(id)s, %(code)s, %(nom)s, %(secteur)s)
                RETURNING client_key
                """,
                r,
            )
            mapping[r["id"]] = cur.fetchone()[0]
    return mapping


def load_dim_site(staging_conn: Any, warehouse_conn: Any) -> dict[int, int]:
    """Charge `Dim_Site` depuis `staging.entrepots`.

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.

    Returns:
        Mapping `entrepots.id` (staging) -> `site_key` (entrepôt).
    """
    rows = _fetch_dicts(
        staging_conn, "SELECT id, code, nom, ville, capacite_palettes FROM entrepots ORDER BY id"
    )
    mapping: dict[int, int] = {}
    with warehouse_conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                INSERT INTO dimensions.dim_site (entrepot_id, code, nom, ville, capacite_palettes)
                VALUES (%(id)s, %(code)s, %(nom)s, %(ville)s, %(capacite_palettes)s)
                RETURNING site_key
                """,
                r,
            )
            mapping[r["id"]] = cur.fetchone()[0]
    return mapping


def load_dim_categorie(staging_conn: Any, warehouse_conn: Any) -> dict[str, int]:
    """Charge `Dim_Categorie` : les catégories distinctes de `staging.produits`.

    Dimension à grain réduit, conformée entre les deux sources de
    `Fait_Expedition` — voir `modelisation_omega_bi.md` §6.3.

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.

    Returns:
        Mapping `produits.categorie` (libellé) -> `categorie_key` (entrepôt).
    """
    rows = _fetch_dicts(
        staging_conn, "SELECT DISTINCT categorie FROM produits ORDER BY categorie"
    )
    mapping: dict[str, int] = {}
    with warehouse_conn.cursor() as cur:
        for r in rows:
            cur.execute(
                "INSERT INTO dimensions.dim_categorie (libelle) VALUES (%(categorie)s) "
                "RETURNING categorie_key",
                r,
            )
            mapping[r["categorie"]] = cur.fetchone()[0]
    return mapping


def load_dim_produit(
    staging_conn: Any, warehouse_conn: Any, categorie_keys: dict[str, int]
) -> dict[int, int]:
    """Charge `Dim_Produit` depuis `staging.produits`.

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.
        categorie_keys: mapping libellé -> `categorie_key`, produit par `load_dim_categorie`.

    Returns:
        Mapping `produits.id` (staging) -> `produit_key` (entrepôt).
    """
    rows = _fetch_dicts(
        staging_conn,
        "SELECT id, sku, libelle, poids_kg, temperature_dirigee, categorie "
        "FROM produits ORDER BY id",
    )
    mapping: dict[int, int] = {}
    with warehouse_conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                INSERT INTO dimensions.dim_produit
                    (produit_id, sku, libelle, poids_kg, temperature_dirigee, categorie_key)
                VALUES
                    (%(id)s, %(sku)s, %(libelle)s, %(poids_kg)s,
                     %(temperature_dirigee)s, %(categorie_key)s)
                RETURNING produit_key
                """,
                {**r, "categorie_key": categorie_keys[r["categorie"]]},
            )
            mapping[r["id"]] = cur.fetchone()[0]
    return mapping


def load_dim_transporteur(staging_conn: Any, warehouse_conn: Any) -> tuple[dict[str, int], int]:
    """Charge `Dim_Transporteur` depuis `staging.transporteurs`, plus le membre « Inconnu ».

    `contact` (donnée personnelle, voir `registre_rgpd.md`) n'est pas
    repris — RGPD *by design*, voir `modelisation_omega_bi.md` §6.5. Le
    membre « Inconnu » (`transporteur_id` NULL) couvre les lignes
    `Fait_Expedition` issues de l'historique, qui ne portent pas cette
    information.

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.

    Returns:
        Un couple (mapping `transporteurs.nom` -> `transporteur_key`,
        `transporteur_key` du membre « Inconnu »). Une clé par nom, pas
        par id : `expeditions.transporteur` (FluxPro) est un texte
        libre, voir `modelisation_omega_bi.md` §5.1.
    """
    rows = _fetch_dicts(staging_conn, "SELECT id, nom FROM transporteurs ORDER BY id")
    mapping: dict[str, int] = {}
    with warehouse_conn.cursor() as cur:
        for r in rows:
            cur.execute(
                "INSERT INTO dimensions.dim_transporteur (transporteur_id, nom) "
                "VALUES (%(id)s, %(nom)s) RETURNING transporteur_key",
                r,
            )
            mapping[r["nom"]] = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO dimensions.dim_transporteur (transporteur_id, nom) "
            "VALUES (NULL, 'Inconnu') RETURNING transporteur_key"
        )
        inconnu_key = cur.fetchone()[0]
    return mapping, inconnu_key


def client_categorie_keys(staging_conn: Any, categorie_keys: dict[str, int]) -> dict[int, int]:
    """Associe chaque `client_id` à la `categorie_key` de ses produits.

    Chaque client de ce jeu de données n'a des produits que dans une
    seule catégorie (vérifié empiriquement en C13,
    `notebooks/exploration_donnees_omega_bi.ipynb` §2) — utilisé pour
    dériver `Fait_Expedition.categorie_key` côté FluxPro/TransFlow, qui
    n'a pas de lien direct vers un produit précis (voir
    `modelisation_omega_bi.md` §5.1).

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        categorie_keys: mapping libellé -> `categorie_key`.

    Returns:
        Mapping `clients.id` -> `categorie_key`.

    Raises:
        ValueError: si un client a des produits dans plusieurs
            catégories — romprait l'hypothèse vérifiée en C13.
    """
    rows = _fetch_dicts(
        staging_conn, "SELECT DISTINCT client_id, categorie FROM produits ORDER BY client_id"
    )
    mapping: dict[int, int] = {}
    for r in rows:
        key = categorie_keys[r["categorie"]]
        if r["client_id"] in mapping and mapping[r["client_id"]] != key:
            raise ValueError(
                f"client_id {r['client_id']} a des produits dans plusieurs catégories "
                "-- hypothèse vérifiée en C13 mise en défaut"
            )
        mapping[r["client_id"]] = key
    return mapping


def load_fait_stock(
    staging_conn: Any, warehouse_conn: Any, site_keys: dict[int, int], produit_keys: dict[int, int]
) -> int:
    """Charge `Fait_Stock` depuis `staging.stocks` (grain entrepôt x produit x date).

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.
        site_keys: mapping `entrepots.id` -> `site_key`.
        produit_keys: mapping `produits.id` -> `produit_key`.

    Returns:
        Le nombre de lignes insérées.
    """
    rows = _fetch_dicts(
        staging_conn, "SELECT entrepot_id, produit_id, quantite, date_maj FROM stocks"
    )
    records = [
        {
            "site_key": site_keys[r["entrepot_id"]],
            "produit_key": produit_keys[r["produit_id"]],
            "date_key": _date_key(r["date_maj"]),
            "quantite_stock": r["quantite"],
        }
        for r in rows
    ]
    with warehouse_conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO exploitation.fait_stock (site_key, produit_key, date_key, quantite_stock)
            VALUES (%(site_key)s, %(produit_key)s, %(date_key)s, %(quantite_stock)s)
            """,
            records,
        )
    return len(records)


def load_fait_commande(
    staging_conn: Any,
    warehouse_conn: Any,
    client_keys: dict[int, int],
    site_keys: dict[int, int],
    produit_keys: dict[int, int],
) -> int:
    """Charge `Fait_Commande` depuis `staging.commandes`/`lignes_commande` (FluxPro).

    Grain ligne de commande. `commandes_clients` n'est volontairement
    pas mobilisée ici — voir `modelisation_omega_bi.md` §6.1.

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.
        client_keys: mapping `clients.id` -> `client_key`.
        site_keys: mapping `entrepots.id` -> `site_key`.
        produit_keys: mapping `produits.id` -> `produit_key`.

    Returns:
        Le nombre de lignes insérées.
    """
    rows = _fetch_dicts(
        staging_conn,
        """
        SELECT c.id AS commande_id, c.client_id, c.entrepot_id, c.date_commande, c.statut,
               lc.produit_id, lc.quantite, p.poids_kg
        FROM commandes c
        JOIN lignes_commande lc ON lc.commande_id = c.id
        JOIN produits p ON p.id = lc.produit_id
        ORDER BY c.id, lc.id
        """,
    )
    records = [
        {
            "client_key": client_keys[r["client_id"]],
            "site_key": site_keys[r["entrepot_id"]],
            "produit_key": produit_keys[r["produit_id"]],
            "date_key": _date_key(r["date_commande"]),
            "commande_id": str(r["commande_id"]),
            "quantite_commandee": r["quantite"],
            "poids_ligne": r["quantite"] * r["poids_kg"] if r["poids_kg"] is not None else None,
            "statut_commande": r["statut"],
        }
        for r in rows
    ]
    with warehouse_conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO commercial.fait_commande
                (client_key, site_key, produit_key, date_key, commande_id,
                 quantite_commandee, poids_ligne, statut_commande)
            VALUES
                (%(client_key)s, %(site_key)s, %(produit_key)s, %(date_key)s, %(commande_id)s,
                 %(quantite_commandee)s, %(poids_ligne)s, %(statut_commande)s)
            """,
            records,
        )
    return len(records)


def load_fait_expedition_fluxpro(
    staging_conn: Any,
    warehouse_conn: Any,
    client_keys: dict[int, int],
    site_keys: dict[int, int],
    client_cat_keys: dict[int, int],
    transporteur_nom_keys: dict[str, int],
) -> int:
    """Charge la partie FluxPro/TransFlow de `Fait_Expedition`.

    `poids_kg` est calculé en sommant `lignes_commande.quantite *
    produits.poids_kg` pour la commande liée (`expeditions` ne porte pas
    de poids directement) ; `categorie_key` est dérivée du client via
    `client_cat_keys` (un client = une catégorie, voir
    `client_categorie_keys`) ; `cout_transport_eur` reste NULL (absent
    de FluxPro/TransFlow, voir `modelisation_omega_bi.md` §5.1) ;
    `livre_a_lheure` réutilise la même définition que
    `datacore.api.repository.taux_service_par_client`
    (`date_livraison_reelle <= date_livraison_prevue`).

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.
        client_keys: mapping `clients.id` -> `client_key`.
        site_keys: mapping `entrepots.id` -> `site_key`.
        client_cat_keys: mapping `clients.id` -> `categorie_key`.
        transporteur_nom_keys: mapping `transporteurs.nom` -> `transporteur_key`.

    Returns:
        Le nombre de lignes insérées.
    """
    rows = _fetch_dicts(
        staging_conn,
        """
        SELECT e.tracking_number, e.transporteur, e.date_expedition,
               e.date_livraison_prevue, e.date_livraison_reelle, e.statut,
               c.client_id, c.entrepot_id,
               (SELECT sum(lc.quantite * p.poids_kg)
                FROM lignes_commande lc JOIN produits p ON p.id = lc.produit_id
                WHERE lc.commande_id = c.id) AS poids_kg
        FROM expeditions e
        JOIN commandes c ON c.id = e.commande_id
        ORDER BY e.id
        """,
    )
    records = []
    for r in rows:
        livree = r["date_livraison_reelle"] is not None
        records.append({
            "client_key": client_keys[r["client_id"]],
            "site_key": site_keys[r["entrepot_id"]],
            "categorie_key": client_cat_keys[r["client_id"]],
            "date_key": _date_key(r["date_expedition"]),
            "transporteur_key": transporteur_nom_keys[r["transporteur"]],
            "tracking_number": r["tracking_number"],
            "source_systeme": "FluxPro_TransFlow",
            "poids_kg": r["poids_kg"],
            "delai_livraison_jours": (
                (r["date_livraison_reelle"] - r["date_expedition"]).days if livree else None
            ),
            "cout_transport_eur": None,
            "statut": r["statut"],
            "livre_a_lheure": (
                r["date_livraison_reelle"] <= r["date_livraison_prevue"] if livree else None
            ),
        })
    with warehouse_conn.cursor() as cur:
        cur.executemany(
            f"""
            INSERT INTO exploitation.fait_expedition ({FAIT_EXPEDITION_COLUMNS})
            VALUES ({FAIT_EXPEDITION_PLACEHOLDERS})
            """,
            records,
        )
    return len(records)


def load_fait_expedition_historique(
    staging_conn: Any,
    warehouse_conn: Any,
    client_nom_keys: dict[str, int],
    site_ville_keys: dict[str, int],
    categorie_keys: dict[str, int],
    transporteur_inconnu_key: int,
) -> tuple[int, int]:
    """Charge la partie historique de `Fait_Expedition`, avec quarantaine des lignes
    non rapprochées.

    `client`/`entrepot`/`categorie_produit` sont du texte libre, non
    garanti par contrainte (voir `modelisation_omega_bi.md` §5.1/§8) :
    toute ligne dont l'une de ces valeurs ne correspond à aucune valeur
    connue est mise en quarantaine (comptée, non insérée) plutôt
    qu'insérée avec une clé fausse. `livre_a_lheure` reste NULL : aucune
    date de livraison prévue n'est disponible dans cette source pour la
    calculer (seul `delai_livraison_jours`, un délai constaté sans seuil
    de référence, y figure).

    Args:
        staging_conn: connexion psycopg2 ouverte sur la base de staging.
        warehouse_conn: connexion psycopg2 ouverte sur l'entrepôt.
        client_nom_keys: mapping `dim_client.nom` -> `client_key`.
        site_ville_keys: mapping `dim_site.ville` -> `site_key`.
        categorie_keys: mapping `dim_categorie.libelle` -> `categorie_key`.
        transporteur_inconnu_key: `transporteur_key` du membre « Inconnu ».

    Returns:
        Un couple (nombre de lignes insérées, nombre de lignes mises en quarantaine).
    """
    rows = _fetch_dicts(
        staging_conn,
        """
        SELECT client, entrepot, categorie_produit, date_expedition,
               poids_kg, delai_livraison_jours, cout_transport_eur, statut
        FROM historique_expeditions
        """,
    )
    records = []
    n_quarantaine = 0
    for r in rows:
        if (
            r["client"] not in client_nom_keys
            or r["entrepot"] not in site_ville_keys
            or r["categorie_produit"] not in categorie_keys
        ):
            n_quarantaine += 1
            continue
        records.append({
            "client_key": client_nom_keys[r["client"]],
            "site_key": site_ville_keys[r["entrepot"]],
            "categorie_key": categorie_keys[r["categorie_produit"]],
            "date_key": _date_key(r["date_expedition"]),
            "transporteur_key": transporteur_inconnu_key,
            "tracking_number": None,
            "source_systeme": "Historique",
            "poids_kg": r["poids_kg"],
            "delai_livraison_jours": r["delai_livraison_jours"],
            "cout_transport_eur": r["cout_transport_eur"],
            "statut": r["statut"],
            "livre_a_lheure": None,
        })
    with warehouse_conn.cursor() as cur:
        cur.executemany(
            f"""
            INSERT INTO exploitation.fait_expedition ({FAIT_EXPEDITION_COLUMNS})
            VALUES ({FAIT_EXPEDITION_PLACEHOLDERS})
            """,
            records,
        )
    return len(records), n_quarantaine


def main() -> None:
    """Exécute le pipeline complet : vide l'entrepôt (hors `dim_temps`) puis recharge tout.

    Transaction unique côté entrepôt : un échec à n'importe quelle étape
    annule (`ROLLBACK`) l'ensemble du rechargement plutôt que de laisser
    l'entrepôt partiellement peuplé.
    """
    staging_conn = psycopg2.connect(STAGING_DB_DSN)
    warehouse_conn = psycopg2.connect(OMEGA_BI_DB_DSN)
    try:
        truncate_warehouse(warehouse_conn)

        client_keys = load_dim_client(staging_conn, warehouse_conn)
        site_keys = load_dim_site(staging_conn, warehouse_conn)
        categorie_keys = load_dim_categorie(staging_conn, warehouse_conn)
        produit_keys = load_dim_produit(staging_conn, warehouse_conn, categorie_keys)
        transporteur_nom_keys, transporteur_inconnu_key = load_dim_transporteur(
            staging_conn, warehouse_conn
        )

        client_nom_keys = _lookup_by_column(
            warehouse_conn, "dimensions.dim_client", "client_key", "nom"
        )
        site_ville_keys = _lookup_by_column(
            warehouse_conn, "dimensions.dim_site", "site_key", "ville"
        )
        client_cat_keys = client_categorie_keys(staging_conn, categorie_keys)

        n_stock = load_fait_stock(staging_conn, warehouse_conn, site_keys, produit_keys)
        n_commande = load_fait_commande(
            staging_conn, warehouse_conn, client_keys, site_keys, produit_keys
        )
        n_exp_fluxpro = load_fait_expedition_fluxpro(
            staging_conn, warehouse_conn, client_keys, site_keys, client_cat_keys,
            transporteur_nom_keys,
        )
        n_exp_hist, n_quarantaine = load_fait_expedition_historique(
            staging_conn, warehouse_conn, client_nom_keys, site_ville_keys, categorie_keys,
            transporteur_inconnu_key,
        )

        warehouse_conn.commit()
        print(
            f"dim_client: {len(client_keys)}, dim_site: {len(site_keys)}, "
            f"dim_categorie: {len(categorie_keys)}, dim_produit: {len(produit_keys)}, "
            f"dim_transporteur: {len(transporteur_nom_keys)} + 1 (Inconnu)\n"
            f"fait_stock: {n_stock}, fait_commande: {n_commande}, "
            f"fait_expedition: {n_exp_fluxpro} (FluxPro/TransFlow) + {n_exp_hist} (Historique)\n"
            f"lignes historique mises en quarantaine: {n_quarantaine}"
        )
    except Exception:
        warehouse_conn.rollback()
        raise
    finally:
        staging_conn.close()
        warehouse_conn.close()


if __name__ == "__main__":
    main()
