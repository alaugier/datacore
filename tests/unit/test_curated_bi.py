"""Tests unitaires de la pseudonymisation HMAC pour l'export curated_bi/ (C21bis).

`pseudonyme` est une fonction pure, testée sans dépendance à une
infrastructure réelle. `construire_curated_bi` (DuckDB + MinIO réels)
est vérifiée en conditions réelles, documentée dans
`docs/architecture/registre_rgpd_lake.md` §2.
"""
import re
from pathlib import Path

import pytest

from datacore.storage.lake.curated_bi import (
    FLUX_A_PSEUDONYMISER,
    VALEUR_EXEMPLE_ENV,
    pseudonyme,
    verifier_cle_configuree,
)


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


# --- Garde-fou sur la clé (suite à la relecture externe sur config.py) ---


def test_verifier_cle_configuree_leve_une_erreur_si_cle_absente():
    """Une clé None (LAKE_PSEUDONYM_KEY non définie) doit être refusée explicitement."""
    with pytest.raises(RuntimeError, match="n'est pas définie"):
        verifier_cle_configuree(None)


def test_verifier_cle_configuree_leve_une_erreur_si_cle_vide():
    """Une clé vide doit être refusée comme une clé absente."""
    with pytest.raises(RuntimeError, match="n'est pas définie"):
        verifier_cle_configuree("")


def test_verifier_cle_configuree_leve_une_erreur_si_valeur_dexemple():
    """La valeur d'exemple de .env.example, oubliée telle quelle, doit être refusée."""
    with pytest.raises(RuntimeError, match="valeur d'exemple"):
        verifier_cle_configuree(VALEUR_EXEMPLE_ENV)


def test_verifier_cle_configuree_accepte_une_vraie_cle():
    """Une clé valide (ni absente, ni la valeur d'exemple) est renvoyée inchangée."""
    assert verifier_cle_configuree("une-vraie-cle-secrete") == "une-vraie-cle-secrete"


def test_pseudonyme_leve_une_erreur_si_cle_non_configuree():
    """Le garde-fou s'applique à pseudonyme() elle-même, pas seulement en amont --
    aucun appel ne peut le contourner, tests compris."""
    with pytest.raises(RuntimeError):
        pseudonyme("VH-001", cle=None)
    with pytest.raises(RuntimeError):
        pseudonyme("VH-001", cle=VALEUR_EXEMPLE_ENV)


def test_valeur_exemple_env_reste_synchronisee_avec_env_example():
    """VALEUR_EXEMPLE_ENV (code) et .env.example (fichier) ne doivent jamais diverger --
    sinon le garde-fou ne détecterait plus l'oubli qu'il est censé détecter."""
    contenu_env_example = Path(__file__).resolve().parents[2].joinpath(".env.example").read_text()
    correspondance = re.search(r"^LAKE_PSEUDONYM_KEY=(.+)$", contenu_env_example, re.MULTILINE)

    assert correspondance is not None, "LAKE_PSEUDONYM_KEY absente de .env.example"
    assert correspondance.group(1) == VALEUR_EXEMPLE_ENV


# --- Scénario de fuite (demandé explicitement en relecture externe) ---


def test_scenario_fuite_vehicule_id_connu_ne_permet_pas_de_deviner_le_pseudonyme_reel():
    """Un attaquant qui connaît vehicule_id en clair (ex. fuite de tournees.vehicule_id)
    mais pas la vraie clé de session ne peut pas reconstituer le pseudonyme réel, même en
    essayant les clés les plus prévisibles (absente, vide, valeur d'exemple oubliée)."""
    vehicule_id_fuite = "VH-001"  # connu de l'attaquant, ex. via tournees.vehicule_id
    cle_reelle_de_session = "cle-secrete-generee-localement-jamais-partagee"

    pseudonyme_reel_dans_curated_bi = pseudonyme(vehicule_id_fuite, cle=cle_reelle_de_session)

    # L'attaquant ne connaît pas la vraie clé : les valeurs les plus prévisibles
    # sont explicitement refusées avant même de produire un résultat exploitable.
    for cle_tentee in (None, "", VALEUR_EXEMPLE_ENV):
        with pytest.raises(RuntimeError):
            pseudonyme(vehicule_id_fuite, cle=cle_tentee)

    # Et si l'attaquant tente malgré tout une clé plausible mais fausse, le résultat
    # ne correspond pas à l'entrée réelle de curated_bi/ construite avec la vraie clé.
    pseudonyme_devine = pseudonyme(vehicule_id_fuite, cle="cle-devinee-par-lattaquant")
    assert pseudonyme_devine != pseudonyme_reel_dans_curated_bi
