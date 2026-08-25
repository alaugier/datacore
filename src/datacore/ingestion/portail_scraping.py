"""Scraping du portail transporteur (page HTML de suivi de colis) (C8).

Couvre la source « page web à scraper » attendue par le référentiel (voir
`docs/architecture/topographie_donnees.md` section 2). Le portail ne
propose aucune API : les données sont extraites en parsant le HTML des
pages de liste et de détail.
"""
from typing import Any

import requests
from bs4 import BeautifulSoup

from datacore.ingestion.config import TRANSFLOW_API_URL


def scrape_colis_list(base_url: str = TRANSFLOW_API_URL) -> list[str]:
    """Récupère les numéros de suivi listés sur la page d'index du portail.

    Args:
        base_url: racine du site à scraper.

    Returns:
        La liste des numéros de suivi (tracking numbers) trouvés.
    """
    resp = requests.get(f"{base_url}/portail-transporteur/colis", timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.select("a[href*='/portail-transporteur/colis/']")
    return [a["href"].rsplit("/", 1)[-1] for a in links]


def scrape_colis_detail(tracking_number: str, base_url: str = TRANSFLOW_API_URL) -> dict[str, Any]:
    """Scrape la fiche de suivi d'un colis.

    Args:
        tracking_number: numéro de suivi du colis à consulter.
        base_url: racine du site à scraper.

    Returns:
        dict avec les clés `tracking_number`, `statut`, `adresse_livraison`,
        `heure_estimee`, `heure_reelle`, `tournee_id`.

    Raises:
        requests.HTTPError: si le colis n'existe pas (404).
    """
    resp = requests.get(f"{base_url}/portail-transporteur/colis/{tracking_number}", timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = {
        row.find("th").get_text(strip=True): row.find("td").get_text(strip=True)
        for row in soup.select("table tr")
    }
    return {
        "tracking_number": tracking_number,
        "statut": rows.get("Statut"),
        "adresse_livraison": rows.get("Adresse de livraison"),
        "heure_estimee": rows.get("Heure estimee"),
        "heure_reelle": rows.get("Heure reelle"),
        "tournee_id": rows.get("Tournee"),
    }
