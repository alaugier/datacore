"""Tests unitaires de la détection de colonnes évoquant une donnée personnelle (C16).

`colonnes_suspectes` est une fonction pure, testée sans dépendance à une
base réelle. `auditer` (introspection SQL) est vérifiée pour de vrai
contre l'entrepôt (Docker Compose), documentée dans
`docs/architecture/registre_rgpd_entrepot.md`.
"""
from datacore.governance.audit_rgpd import colonnes_suspectes


def test_detecte_les_colonnes_personnelles_connues():
    """Les 3 colonnes personnelles déjà identifiées en C11 sont bien détectées."""
    colonnes = ["id", "chauffeur", "adresse_livraison", "contact", "date"]

    assert colonnes_suspectes(colonnes) == ["chauffeur", "adresse_livraison", "contact"]


def test_ne_signale_pas_les_noms_dentreprise():
    """nom/libelle/code (client, site, transporteur, catégorie) ne sont pas des personnes."""
    colonnes = ["client_key", "nom", "code", "libelle", "secteur", "ville"]

    assert colonnes_suspectes(colonnes) == []


def test_detecte_insensible_a_la_casse():
    """La détection ne dépend pas de la casse du nom de colonne."""
    assert colonnes_suspectes(["CHAUFFEUR", "Adresse_Livraison"]) == [
        "CHAUFFEUR", "Adresse_Livraison",
    ]


def test_liste_vide_sans_colonne_suspecte():
    """Aucune colonne suspecte : liste vide, pas d'erreur."""
    assert colonnes_suspectes([]) == []
