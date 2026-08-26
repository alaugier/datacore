"""Nettoyage et agrégation des fichiers clients bruts en un jeu de données unique (C10).

Prend en entrée les enregistrements bruts lus par C8
(`datacore.ingestion.clients_files`) et produit un jeu de données
consolidé, dans un schéma commun aux trois clients (NordDrive,
FreshMarket, MedioTex) :

- suppression des entrées corrompues (quantité manquante ou non numérique) ;
- homogénéisation des formats de date (trois formats rencontrés dans les
  fichiers sources : `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD`) vers ISO 8601 ;
- homogénéisation des unités (poids NordDrive en grammes -> kg, cohérent
  avec `produits.poids_kg` de FluxPro) ;
- suppression des doublons (même commande + même produit), avec
  résolution des conflits (valeurs différentes pour un même couple)
  par conservation de la dernière occurrence rencontrée.

Note méthodologique (corrige `docs/architecture/topographie_donnees.md`
§3.3) : un identifiant de commande répété dans un fichier client
correspond très majoritairement à une commande multi-produits légitime
(plusieurs lignes, un produit par ligne — comme `lignes_commande` dans
FluxPro), pas à un doublon. Le vrai doublon se mesure au grain
(commande, produit) : c'est ce grain qu'utilise `deduplicate()`.
"""
import datetime
from typing import Any

DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")


def parse_date(raw: str) -> str:
    """Normalise une date exprimée dans l'un des trois formats rencontrés en ISO 8601.

    Args:
        raw: date brute, ex. "16/05/2026", "15-06-2026" ou "2025-03-07".

    Returns:
        La date au format ISO "YYYY-MM-DD".

    Raises:
        ValueError: si `raw` ne correspond à aucun des formats connus.
    """
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Format de date non reconnu : {raw!r}")


def _parse_quantite(raw: str | None) -> int | None:
    """Convertit une quantité brute en entier, ou None si absente/invalide.

    Args:
        raw: valeur brute de la colonne quantité.

    Returns:
        L'entier correspondant, ou None si la valeur est vide ou non
        numérique (cas traité comme une entrée corrompue par l'appelant).
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def clean_norddrive(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nettoie et convertit les commandes NordDrive vers le schéma unifié.

    Args:
        records: lignes brutes telles que lues par
            `datacore.ingestion.clients_files.read_norddrive`.

    Returns:
        Les lignes valides, converties au schéma unifié (poids en kg).
        Les lignes à quantité manquante/invalide sont écartées.
    """
    cleaned = []
    for r in records:
        qte = _parse_quantite(r.get("qte"))
        if qte is None:
            continue
        cleaned.append(
            {
                "client": "NordDrive",
                "commande_id": r["ref_commande"],
                "date_commande": parse_date(r["date_cde"]),
                "sku": r["reference_piece"],
                "libelle_produit": r["designation"],
                "quantite": qte,
                "poids_kg": round(int(r["poids_unitaire_g"]) / 1000, 3),
                "entrepot": r["entrepot"],
                "chaine_froid_requise": None,
            }
        )
    return cleaned


def clean_freshmarket(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nettoie et convertit les commandes FreshMarket vers le schéma unifié.

    Args:
        records: lignes brutes telles que lues par
            `datacore.ingestion.clients_files.read_freshmarket`.

    Returns:
        Les lignes valides, converties au schéma unifié (booléen chaîne du
        froid). Les lignes à quantité manquante/invalide sont écartées.
    """
    cleaned = []
    for r in records:
        qte = _parse_quantite(r.get("quantite_commandee"))
        if qte is None:
            continue
        cleaned.append(
            {
                "client": "FreshMarket",
                "commande_id": r["id_commande_client"],
                "date_commande": parse_date(r["date_reception"]),
                "sku": r["code_article"],
                "libelle_produit": r["libelle_produit"],
                "quantite": qte,
                "poids_kg": None,
                "entrepot": r["site_livraison"],
                "chaine_froid_requise": r["chaine_froid_requise"].strip().upper() == "OUI",
            }
        )
    return cleaned


def clean_mediotex(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nettoie et convertit les commandes MedioTex vers le schéma unifié.

    Args:
        records: lignes brutes telles que lues par
            `datacore.ingestion.clients_files.read_mediotex`.

    Returns:
        Les lignes valides, converties au schéma unifié. Les lignes à
        quantité manquante/invalide sont écartées.
    """
    cleaned = []
    for r in records:
        qte = _parse_quantite(r.get("quantite"))
        if qte is None:
            continue
        cleaned.append(
            {
                "client": "MedioTex",
                "commande_id": r["numero_cde"],
                "date_commande": parse_date(r["date"]),
                "sku": r["sku"],
                "libelle_produit": r["description"],
                "quantite": qte,
                "poids_kg": None,
                "entrepot": r["entrepot_destination"],
                "chaine_froid_requise": None,
            }
        )
    return cleaned


def deduplicate(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Supprime les doublons au grain (client, commande, produit).

    En cas de conflit (valeurs différentes pour un même couple
    commande/produit, ex. quantité différente selon la ligne), la
    dernière occurrence rencontrée dans le fichier source est conservée
    ("dernière valeur gagne"), et le conflit est comptabilisé pour
    traçabilité.

    Args:
        records: enregistrements déjà convertis au schéma unifié (via
            `clean_norddrive`/`clean_freshmarket`/`clean_mediotex`).

    Returns:
        tuple (liste dédupliquée, nombre de conflits résolus).
    """
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    conflicts = 0
    for r in records:
        key = (r["client"], r["commande_id"], r["sku"])
        if key in by_key and by_key[key] != r:
            conflicts += 1
        by_key[key] = r
    return list(by_key.values()), conflicts


def clean_and_aggregate(
    norddrive_raw: list[dict[str, Any]],
    freshmarket_raw: list[dict[str, Any]],
    mediotex_raw: list[dict[str, Any]],
) -> dict[str, Any]:
    """Nettoie et fusionne les trois fichiers clients en un jeu de données unique.

    Args:
        norddrive_raw: lignes brutes NordDrive.
        freshmarket_raw: lignes brutes FreshMarket.
        mediotex_raw: lignes brutes MedioTex.

    Returns:
        dict avec les clés "records" (jeu de données consolidé, schéma
        unifié) et "rapport" (statistiques de nettoyage : lignes lues par
        source, entrées corrompues supprimées, doublons supprimés,
        conflits résolus).
    """
    raw_counts = {
        "norddrive": len(norddrive_raw),
        "freshmarket": len(freshmarket_raw),
        "mediotex": len(mediotex_raw),
    }
    cleaned = (
        clean_norddrive(norddrive_raw)
        + clean_freshmarket(freshmarket_raw)
        + clean_mediotex(mediotex_raw)
    )
    corrompues = sum(raw_counts.values()) - len(cleaned)
    deduped, conflicts = deduplicate(cleaned)
    return {
        "records": deduped,
        "rapport": {
            "lignes_lues": raw_counts,
            "lignes_corrompues_supprimees": corrompues,
            "doublons_supprimes": len(cleaned) - len(deduped),
            "conflits_resolus": conflicts,
        },
    }
