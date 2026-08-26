"""Tests unitaires du nettoyage et de l'agrégation des fichiers clients (C10).

Les scénarios reproduisent les cas réels observés dans le jeu de données
(voir `docs/architecture/topographie_donnees.md` §3.3) : commandes
multi-produits légitimes, vrais doublons (même commande + même produit)
avec conflit de valeurs, doublons de pure forme (date différemment
formatée), et lignes corrompues (quantité manquante).
"""
import pytest

from datacore.processing.clients_cleaning import (
    clean_and_aggregate,
    deduplicate,
    normalize_freshmarket,
    normalize_mediotex,
    normalize_norddrive,
    parse_date,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("16/05/2026", "2026-05-16"),
        ("15-06-2026", "2026-06-15"),
        ("2025-03-07", "2025-03-07"),
    ],
)
def test_parse_date_handles_all_three_formats(raw, expected):
    """Les trois formats de date rencontrés dans les fichiers clients sont reconnus."""
    assert parse_date(raw) == expected


def test_parse_date_rejects_unknown_format():
    """Un format non reconnu lève une erreur explicite plutôt qu'un résultat silencieux."""
    with pytest.raises(ValueError):
        parse_date("07.03.2025")


def test_normalize_norddrive_converts_grams_to_kg():
    """Le poids NordDrive (grammes) est converti en kg, cohérent avec FluxPro."""
    raw = [
        {
            "ref_commande": "ND-000001",
            "date_cde": "19-07-2026",
            "reference_piece": "SKU-10005",
            "designation": "Bougie d'allumage",
            "qte": "17",
            "poids_unitaire_g": "5900",
            "entrepot": "OMG-LIL",
        }
    ]

    normalized = normalize_norddrive(raw)

    assert normalized[0]["poids_kg"] == 5.9
    assert normalized[0]["client"] == "NordDrive"
    assert normalized[0]["quantite"] == 17


def test_normalize_norddrive_drops_rows_with_missing_quantite():
    """Une ligne sans quantité est une entrée corrompue, écartée."""
    raw = [
        {
            "ref_commande": "ND-000002",
            "date_cde": "19-07-2026",
            "reference_piece": "SKU-10005",
            "designation": "Bougie d'allumage",
            "qte": "",
            "poids_unitaire_g": "5900",
            "entrepot": "OMG-LIL",
        }
    ]

    assert normalize_norddrive(raw) == []


def test_normalize_freshmarket_converts_oui_non_to_boolean():
    """Le booléen métier OUI/NON est converti en bool Python."""
    raw = [
        {
            "id_commande_client": "FM-000821",
            "date_reception": "06-04-2025",
            "code_article": "SKU-20011",
            "libelle_produit": "Yaourt nature 4x125g",
            "quantite_commandee": "28",
            "chaine_froid_requise": "OUI",
            "site_livraison": "OMG-MAR",
        }
    ]

    normalized = normalize_freshmarket(raw)

    assert normalized[0]["chaine_froid_requise"] is True
    assert normalized[0]["poids_kg"] is None


def test_normalize_mediotex_maps_columns_to_unified_schema():
    """Les colonnes MedioTex sont correctement projetées sur le schéma unifié."""
    raw = [
        {
            "numero_cde": "MTX-000159",
            "date": "07/06/2026",
            "sku": "SKU-30027",
            "description": "Short de sport",
            "quantite": "17",
            "entrepot_destination": "OMG-LIL",
        }
    ]

    normalized = normalize_mediotex(raw)

    assert normalized[0]["client"] == "MedioTex"
    assert normalized[0]["sku"] == "SKU-30027"
    assert normalized[0]["date_commande"] == "2026-06-07"


def test_deduplicate_keeps_legitimate_multi_product_orders():
    """Une commande multi-produits (plusieurs SKU différents) n'est pas un doublon."""
    records = [
        {"client": "NordDrive", "commande_id": "ND-000549", "sku": "SKU-10005", "quantite": 17},
        {"client": "NordDrive", "commande_id": "ND-000549", "sku": "SKU-10004", "quantite": 40},
        {"client": "NordDrive", "commande_id": "ND-000549", "sku": "SKU-10003", "quantite": 27},
    ]

    deduped, conflicts = deduplicate(records)

    assert len(deduped) == 3
    assert conflicts == 0


def test_deduplicate_resolves_conflicting_duplicate_with_last_value():
    """Un vrai doublon (même commande + même produit) avec quantités différentes
    est résolu en conservant la dernière occurrence, et compté comme conflit."""
    records = [
        {"client": "NordDrive", "commande_id": "ND-001297", "sku": "SKU-10008", "quantite": 6},
        {"client": "NordDrive", "commande_id": "ND-001297", "sku": "SKU-10008", "quantite": 3},
    ]

    deduped, conflicts = deduplicate(records)

    assert len(deduped) == 1
    assert deduped[0]["quantite"] == 3
    assert conflicts == 1


def test_deduplicate_collapses_pure_formatting_duplicate_without_conflict():
    """Deux lignes identiques une fois normalisées ne comptent pas comme un conflit."""
    records = [
        {"client": "MedioTex", "commande_id": "MTX-000265", "sku": "SKU-30026", "quantite": 20},
        {"client": "MedioTex", "commande_id": "MTX-000265", "sku": "SKU-30026", "quantite": 20},
    ]

    deduped, conflicts = deduplicate(records)

    assert len(deduped) == 1
    assert conflicts == 0


def test_clean_and_aggregate_produces_unique_dataset_and_report():
    """L'agrégation des trois clients produit un jeu unique et un rapport de nettoyage."""
    norddrive_raw = [
        {
            "ref_commande": "ND-000001",
            "date_cde": "19-07-2026",
            "reference_piece": "SKU-10005",
            "designation": "Bougie",
            "qte": "17",
            "poids_unitaire_g": "5900",
            "entrepot": "OMG-LIL",
        },
        {
            "ref_commande": "ND-000002",
            "date_cde": "19-07-2026",
            "reference_piece": "SKU-10004",
            "designation": "Filtre",
            "qte": "",  # corrompue
            "poids_unitaire_g": "1820",
            "entrepot": "OMG-LIL",
        },
    ]
    freshmarket_raw = [
        {
            "id_commande_client": "FM-000821",
            "date_reception": "06-04-2025",
            "code_article": "SKU-20011",
            "libelle_produit": "Yaourt",
            "quantite_commandee": "28",
            "chaine_froid_requise": "OUI",
            "site_livraison": "OMG-MAR",
        },
    ]
    mediotex_raw = []

    result = clean_and_aggregate(norddrive_raw, freshmarket_raw, mediotex_raw)

    assert len(result["records"]) == 2
    assert result["rapport"]["lignes_lues"] == {
        "norddrive": 2,
        "freshmarket": 1,
        "mediotex": 0,
    }
    assert result["rapport"]["lignes_corrompues_supprimees"] == 1
    assert result["rapport"]["doublons_supprimes"] == 0
    assert result["rapport"]["conflits_resolus"] == 0
