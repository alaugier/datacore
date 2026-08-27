"""Tests d'intégration du connecteur TransFlow (C8).

Utilisent la fixture `live_api_mock` (serveur Flask réel en
arrière-plan) plutôt que le client de test Flask, pour vérifier le
comportement HTTP réel : authentification, pagination, filtres.
"""
from datacore.ingestion.transflow import fetch_livraisons, fetch_tournees, fetch_transporteurs


def test_fetch_transporteurs(live_api_mock):
    """Les 3 transporteurs fictifs sont récupérés."""
    transporteurs = fetch_transporteurs(base_url=live_api_mock)

    assert len(transporteurs) == 3


def test_fetch_tournees_aggregates_all_pages(live_api_mock):
    """Toutes les tournées sont récupérées malgré la pagination (139 au total)."""
    tournees = fetch_tournees(base_url=live_api_mock)

    assert len(tournees) == 139


def test_fetch_tournees_filters_by_date(live_api_mock):
    """Le filtre date restreint bien les résultats."""
    all_tournees = fetch_tournees(base_url=live_api_mock)
    a_date = all_tournees[0]["date"]

    filtered = fetch_tournees(date=a_date, base_url=live_api_mock)

    assert filtered
    assert all(t["date"] == a_date for t in filtered)
    assert len(filtered) <= len(all_tournees)


def test_fetch_livraisons_aggregates_all_pages(live_api_mock):
    """Toutes les livraisons sont récupérées malgré la pagination (1100 au total)."""
    livraisons = fetch_livraisons(base_url=live_api_mock)

    assert len(livraisons) == 1100


def test_fetch_livraisons_filters_by_statut(live_api_mock):
    """Le filtre statut ne renvoie que les livraisons du statut demandé."""
    livrees = fetch_livraisons(statut="Livree", base_url=live_api_mock)

    assert livrees
    assert all(liv["statut"] == "Livree" for liv in livrees)
