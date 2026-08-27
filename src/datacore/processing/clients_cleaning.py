"""Nettoyage et agrégation des fichiers clients bruts en un jeu de données unique (C10).

Prend en entrée les enregistrements bruts lus par C8
(`datacore.ingestion.clients_files`) et produit un jeu de données
consolidé, dans un schéma commun aux trois clients (NordDrive,
FreshMarket, MedioTex) :

- `normalize_norddrive`/`normalize_freshmarket`/`normalize_mediotex` :
  normalisent chaque fichier vers le schéma unifié (voir plus bas) — ce
  sont des fonctions de *normalisation* (mapping de colonnes, formats,
  unités), pas seulement de nettoyage ; elles écartent au passage les
  lignes qu'il est impossible de normaliser (quantité manquante ou non
  numérique), traitées comme des entrées corrompues.
- `deduplicate` : supprime les vrais doublons (voir note méthodologique
  ci-dessous) et résout les conflits de valeurs.
- `clean_and_aggregate` : orchestre les deux étapes précédentes sur les
  trois fichiers et produit le jeu de données consolidé final.

Schéma unifié produit : `client`, `commande_id`, `date_commande` (ISO
8601), `sku`, `libelle_produit`, `quantite`, `poids_kg`, `entrepot`,
`chaine_froid_requise`.

Sur le champ `sku` : les trois fichiers désignent le même concept sous
des noms de colonnes différents (`reference_piece` chez NordDrive,
`code_article` chez FreshMarket, `sku` chez MedioTex) : dans les trois
cas, il s'agit du SKU (Stock Keeping Unit) — la référence unique d'un
produit tel que catalogué côté FluxPro (`produits.sku`, voir
[topographie des données §1](../../../docs/architecture/topographie_donnees.md)).
C'est ce même référentiel produit qui est commandé par les trois
clients ; le schéma unifié les regroupe donc tous sous un champ `sku`
unique, condition nécessaire au rapprochement avec FluxPro lors de la
modélisation de la base de travail (C11).

Note méthodologique (corrige `docs/architecture/topographie_donnees.md`
§3.3) : un identifiant de commande répété dans un fichier client
correspond très majoritairement à une commande multi-produits légitime
(plusieurs lignes, un produit par ligne — comme `lignes_commande` dans
FluxPro), pas à un doublon. Le vrai doublon se mesure au grain
(commande, produit) : c'est ce grain qu'utilise `deduplicate()`. Cette
analyse est reproductible dans
`notebooks/exploration_fichiers_clients.ipynb`, qui documente pas à pas
comment les chiffres cités ici et dans la topographie des données ont
été obtenus.
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


def normalize_norddrive(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise les commandes NordDrive vers le schéma unifié.

    Convertit le poids (grammes -> kg) et la date (format libre -> ISO).
    Une ligne dont la quantité est manquante ou non numérique ne peut pas
    être normalisée : elle est écartée (entrée corrompue).

    Args:
        records: lignes brutes telles que lues par
            `datacore.ingestion.clients_files.read_norddrive`.

    Returns:
        Les lignes valides, converties au schéma unifié (poids en kg).
    """
    normalized = []
    for r in records:
        qte = _parse_quantite(r.get("qte"))
        if qte is None:
            continue
        normalized.append(
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
    return normalized


def normalize_freshmarket(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise les commandes FreshMarket vers le schéma unifié.

    Convertit le booléen métier OUI/NON en `bool` Python et la date
    (format libre -> ISO). Une ligne dont la quantité est manquante ou
    non numérique ne peut pas être normalisée : elle est écartée (entrée
    corrompue).

    Args:
        records: lignes brutes telles que lues par
            `datacore.ingestion.clients_files.read_freshmarket`.

    Returns:
        Les lignes valides, converties au schéma unifié (booléen chaîne
        du froid).
    """
    normalized = []
    for r in records:
        qte = _parse_quantite(r.get("quantite_commandee"))
        if qte is None:
            continue
        normalized.append(
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
    return normalized


def normalize_mediotex(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise les commandes MedioTex vers le schéma unifié.

    Projette les colonnes (déjà proches du modèle FluxPro) sur le schéma
    unifié et convertit la date (format libre -> ISO). Une ligne dont la
    quantité est manquante ou non numérique ne peut pas être normalisée :
    elle est écartée (entrée corrompue).

    Args:
        records: lignes brutes telles que lues par
            `datacore.ingestion.clients_files.read_mediotex`.

    Returns:
        Les lignes valides, converties au schéma unifié.
    """
    normalized = []
    for r in records:
        qte = _parse_quantite(r.get("quantite"))
        if qte is None:
            continue
        normalized.append(
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
    return normalized


def deduplicate(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Supprime les doublons au grain (client, commande, produit).

    En cas de conflit (valeurs différentes pour un même couple
    commande/produit, ex. quantité différente selon la ligne), la
    dernière occurrence rencontrée dans le fichier source est conservée
    ("dernière valeur gagne").

    Hypothèse métier retenue et ses limites : les fichiers clients ne
    portent pas d'horodatage précis (heure), seulement une date ; il est
    donc impossible de déterminer avec certitude, à partir des seules
    données disponibles, si un conflit provient d'une erreur de saisie
    ou d'une mise à jour légitime de la commande transmise par le client
    (ex. correction de quantité reçue le même jour). On retient
    conventionnellement l'hypothèse que la dernière ligne rencontrée
    reflète l'état le plus récent transmis par le client — hypothèse
    raisonnable mais non prouvable en l'état, à confirmer avec les
    référents clients en conditions réelles. Chaque conflit est
    comptabilisé (voir `conflits_resolus` dans le rapport de
    `clean_and_aggregate`) pour rester traçable et auditable, plutôt que
    résolu silencieusement.

    Args:
        records: enregistrements déjà normalisés au schéma unifié (via
            `normalize_norddrive`/`normalize_freshmarket`/`normalize_mediotex`).

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
    normalized = (
        normalize_norddrive(norddrive_raw)
        + normalize_freshmarket(freshmarket_raw)
        + normalize_mediotex(mediotex_raw)
    )
    corrompues = sum(raw_counts.values()) - len(normalized)
    deduped, conflicts = deduplicate(normalized)
    return {
        "records": deduped,
        "rapport": {
            "lignes_lues": raw_counts,
            "lignes_corrompues_supprimees": corrompues,
            "doublons_supprimes": len(normalized) - len(deduped),
            "conflits_resolus": conflicts,
        },
    }
