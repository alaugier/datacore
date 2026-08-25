"""Tests d'intégration du scraping du portail transporteur (C8)."""
import pytest
import requests

from datacore.ingestion.portail_scraping import scrape_colis_detail, scrape_colis_list


def test_scrape_colis_list_returns_tracking_numbers(live_api_mock):
    """La page d'index expose des numéros de suivi (échantillon de colis)."""
    tracking_numbers = scrape_colis_list(base_url=live_api_mock)

    assert len(tracking_numbers) > 0
    assert all(tn.startswith("OMG") for tn in tracking_numbers)


def test_scrape_colis_detail_returns_expected_fields(live_api_mock):
    """La fiche détail d'un colis expose statut, adresse et horaires."""
    tracking_number = scrape_colis_list(base_url=live_api_mock)[0]

    detail = scrape_colis_detail(tracking_number, base_url=live_api_mock)

    assert detail["tracking_number"] == tracking_number
    assert detail["statut"] in {"Livree", "En cours"}
    assert detail["adresse_livraison"]
    assert detail["tournee_id"]


def test_scrape_colis_detail_unknown_tracking_raises(live_api_mock):
    """Un numéro de suivi inconnu lève une erreur HTTP (404)."""
    with pytest.raises(requests.HTTPError):
        scrape_colis_detail("UNKNOWN-TRACKING", base_url=live_api_mock)
