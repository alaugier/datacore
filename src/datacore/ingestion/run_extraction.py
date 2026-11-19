#!/usr/bin/env python3
"""Orchestre l'extraction des cinq sources du programme DATA CORE et les
dépose dans la zone d'atterrissage intermédiaire `data/interim/` (C8).

Lancement :
    python3 -m datacore.ingestion.run_extraction

Prérequis : l'API mock TransFlow doit être lancée (voir README), et la
base de staging PostgreSQL doit contenir les données FluxPro (voir
`scripts/init_staging_db.sh`, issue #7) pour l'extraction FluxPro.
"""
import requests

from datacore.config import INTERIM_DIR
from datacore.governance.journal import journaliser
from datacore.ingestion import clients_files, fluxpro, historique, portail_scraping, transflow
from datacore.ingestion.landing import write_records
from datacore.storage.lake.monitoring import _maintenant_utc, enregistrer_scraping_portail


def extract_transflow() -> None:
    """Extrait transporteurs, tournées et livraisons TransFlow vers `data/interim/`."""
    write_records(transflow.fetch_transporteurs(), INTERIM_DIR / "transflow_transporteurs.json")
    write_records(transflow.fetch_tournees(), INTERIM_DIR / "transflow_tournees.json")
    write_records(transflow.fetch_livraisons(), INTERIM_DIR / "transflow_livraisons.json")


def extract_portail() -> None:
    """Scrape le portail transporteur (liste + détail de chaque colis) vers `data/interim/`.

    Journalise un relevé minimal dans `gouvernance.journal_operations`
    (réutilise le mécanisme existant de C16, issue #104) : nombre de
    colis scrapés avec succès, nombre d'erreurs HTTP (404 notamment),
    durée (début/fin déjà suivis par `journaliser()`). Avant ce relevé,
    aucun suivi du scraping ne survivait à l'exécution (voir
    `synthese_technique_oral.md`).

    Duplique aussi ce relevé dans `monitoring.scraping_portail`, lisible
    par Grafana (`bi_reader`) contrairement à `gouvernance.journal_operations`
    -- voir le docstring de `monitoring.enregistrer_scraping_portail()`.
    Le journal d'audit ci-dessus reste la trace de référence, inchangée.
    """
    # UTC, pas l'heure locale : releve_le alimente monitoring.scraping_portail,
    # comparé en UTC par $__timeFilter côté Grafana (voir monitoring._maintenant_utc).
    debut = _maintenant_utc()
    with journaliser("extraction_portail_scraping") as contexte:
        tracking_numbers = portail_scraping.scrape_colis_list()
        details = []
        erreurs = 0
        for tn in tracking_numbers:
            try:
                details.append(portail_scraping.scrape_colis_detail(tn))
            except requests.HTTPError:
                erreurs += 1
        write_records(details, INTERIM_DIR / "portail_colis.json")
        contexte["details"] = f"{len(details)} colis scrapés, {erreurs} erreur(s) HTTP"

    fin = _maintenant_utc()
    duree_ms = int((fin - debut).total_seconds() * 1000)
    enregistrer_scraping_portail(len(details), erreurs, duree_ms, fin)


def extract_fluxpro() -> None:
    """Extrait les 7 tables FluxPro depuis la base de staging vers `data/interim/`."""
    conn = fluxpro.connect()
    try:
        for table in fluxpro.FLUXPRO_TABLES:
            write_records(fluxpro.fetch_table(conn, table), INTERIM_DIR / f"fluxpro_{table}.json")
    finally:
        conn.close()


def extract_clients() -> None:
    """Lit les trois fichiers clients bruts vers `data/interim/`."""
    for name, records in clients_files.read_all_clients().items():
        write_records(records, INTERIM_DIR / f"clients_{name}.json")


def extract_historique() -> None:
    """Lit l'historique d'expéditions vers `data/interim/`."""
    write_records(historique.read_historique(), INTERIM_DIR / "historique.json")


def main() -> None:
    """Lance l'ensemble des extractions et affiche un résumé."""
    steps = {
        "TransFlow (API)": extract_transflow,
        "Portail transporteur (scraping)": extract_portail,
        "FluxPro (base de staging)": extract_fluxpro,
        "Fichiers clients": extract_clients,
        "Historique": extract_historique,
    }
    for label, step in steps.items():
        print(f"Extraction : {label}...")
        step()
    print(f"Terminé. Fichiers écrits dans {INTERIM_DIR}")


if __name__ == "__main__":
    main()
