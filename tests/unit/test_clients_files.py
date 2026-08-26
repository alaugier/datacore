"""Tests unitaires de la lecture brute des fichiers clients (C8).

Utilisent de petits extraits synthétiques reproduisant les particularités
de format documentées dans `docs/architecture/topographie_donnees.md`
(délimiteurs, colonnes) plutôt que le jeu de données réel `data/raw/`,
non versionné et donc absent en CI.
"""
from datacore.ingestion.clients_files import read_freshmarket, read_mediotex, read_norddrive


def test_read_norddrive_semicolon_delimiter(tmp_path):
    """Le fichier NordDrive utilise un délimiteur point-virgule."""
    csv_content = (
        "ref_commande;date_cde;reference_piece;designation;qte;poids_unitaire_g;entrepot\n"
        "ND-000001;19-07-2026;SKU-10005;Bougie d'allumage;17;5900;OMG-LIL\n"
    )
    path = tmp_path / "norddrive_commandes.csv"
    path.write_text(csv_content, encoding="utf-8")

    rows = read_norddrive(path)

    assert len(rows) == 1
    assert rows[0]["ref_commande"] == "ND-000001"
    assert rows[0]["entrepot"] == "OMG-LIL"


def test_read_freshmarket_comma_delimiter(tmp_path):
    """Le fichier FreshMarket utilise un délimiteur virgule et un booléen métier OUI/NON."""
    csv_content = (
        "id_commande_client,date_reception,code_article,libelle_produit,"
        "quantite_commandee,chaine_froid_requise,site_livraison\n"
        "FM-000821,06-04-2025,SKU-20011,Yaourt nature 4x125g,28,OUI,OMG-MAR\n"
    )
    path = tmp_path / "freshmarket_commandes.csv"
    path.write_text(csv_content, encoding="utf-8")

    rows = read_freshmarket(path)

    assert len(rows) == 1
    assert rows[0]["chaine_froid_requise"] == "OUI"


def test_read_mediotex_comma_delimiter(tmp_path):
    """Le fichier MedioTex utilise déjà des noms de colonnes proches du modèle FluxPro."""
    csv_content = (
        "numero_cde,date,sku,description,quantite,entrepot_destination\n"
        "MTX-000159,07/06/2026,SKU-30027,Short de sport,17,OMG-LIL\n"
    )
    path = tmp_path / "mediotex_commandes.csv"
    path.write_text(csv_content, encoding="utf-8")

    rows = read_mediotex(path)

    assert len(rows) == 1
    assert rows[0]["sku"] == "SKU-30027"
