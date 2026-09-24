"""Tests unitaires de la pseudonymisation HMAC pour l'export curated_bi/ (C21bis).

`pseudonyme` est une fonction pure, testée sans dépendance à une
infrastructure réelle. `construire_curated_bi` (DuckDB + MinIO réels)
est vérifiée en conditions réelles, documentée dans
`docs/architecture/registre_rgpd_lake.md` §2.
"""
from datacore.storage.lake.curated_bi import FLUX_A_PSEUDONYMISER, pseudonyme


def test_pseudonyme_est_stable_pour_le_meme_identifiant():
    """Le même vehicule_id produit toujours le même pseudonyme (continuité analytique)."""
    assert pseudonyme("VH-001", cle="cle-de-test") == pseudonyme("VH-001", cle="cle-de-test")


def test_pseudonyme_differe_entre_identifiants_distincts():
    """Deux véhicules différents ne doivent pas produire le même pseudonyme."""
    assert pseudonyme("VH-001", cle="cle-de-test") != pseudonyme("VH-002", cle="cle-de-test")


def test_pseudonyme_depend_de_la_cle():
    """Sans la bonne clé, le pseudonyme obtenu est différent -- la clé est bien nécessaire."""
    assert pseudonyme("VH-001", cle="cle-a") != pseudonyme("VH-001", cle="cle-b")


def test_pseudonyme_nest_pas_un_hash_simple_devinable():
    """Un hash sans clé (sha256 brut) serait recalculable par force brute sur 15 véhicules --
    vérifie que le pseudonyme ne correspond pas à un sha256 non-keyé de l'identifiant seul."""
    import hashlib

    hash_nu = hashlib.sha256(b"VH-001").hexdigest()[:16]
    assert pseudonyme("VH-001", cle="cle-de-test") != hash_nu


def test_pseudonyme_ne_revele_pas_lidentifiant_original():
    """Le pseudonyme ne contient pas l'identifiant d'origine en clair."""
    assert "VH-001" not in pseudonyme("VH-001", cle="cle-de-test")


def test_flux_a_pseudonymiser_couvre_bien_les_2_flux_geolocalisation():
    """Garde-fou : seuls les 2 flux portant vehicule_id sont concernés."""
    assert set(FLUX_A_PSEUDONYMISER) == {"geoloc_flotte", "flux_sse_capteurs"}
