"""Tests unitaires de la lecture de l'historique d'expéditions (C8)."""
from datacore.ingestion.historique import read_historique


def test_read_historique(tmp_path):
    """Lit un extrait d'historique et préserve toutes les colonnes."""
    csv_content = (
        "id,client,entrepot,categorie_produit,date_expedition,poids_kg,"
        "delai_livraison_jours,cout_transport_eur,statut\n"
        "1,MedioTex,Marseille,Textile,2024-04-11,29.83,1,52.37,Retardee\n"
    )
    path = tmp_path / "historique.csv"
    path.write_text(csv_content, encoding="utf-8")

    rows = read_historique(path)

    assert len(rows) == 1
    assert rows[0]["client"] == "MedioTex"
    assert rows[0]["statut"] == "Retardee"
