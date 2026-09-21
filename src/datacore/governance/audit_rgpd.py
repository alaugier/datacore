#!/usr/bin/env python3
"""Audit RGPD de l'entrepôt OMEGA BI (C16).

Vérifie par introspection du schéma réel de la base qu'aucune colonne
évoquant une donnée personnelle n'a été introduite — un contrôle
répétable à chaque revue, pas une conclusion figée une fois pour toutes
dans la documentation. Voir
`docs/architecture/registre_rgpd_entrepot.md` pour l'analyse complète
et le résultat de référence (aucune donnée personnelle trouvée à ce
jour).

Lancement :
    python3 -m datacore.governance.audit_rgpd
"""
import re

import psycopg2

from datacore.config import OMEGA_BI_DB_DSN

# Motifs de noms de colonnes évoquant une donnée personnelle -- mêmes
# catégories que celles réellement trouvées dans la base de travail
# (C11, voir registre_rgpd.md §1) : personne physique nommée,
# coordonnées, adresse. `nom`/`libelle` seuls ne sont volontairement pas
# suspects : ce sont des noms d'entreprises/entités (client, site,
# transporteur, catégorie), pas de personnes.
MOTIFS_SUSPECTS = [
    r"chauffeur", r"conducteur", r"driver",
    r"adresse", r"^contact$", r"telephone", r"email", r"courriel",
    r"nom_complet", r"prenom",
]

SCHEMAS_AUDITES = ("dimensions", "exploitation", "commercial", "gouvernance")


def colonnes_suspectes(noms_colonnes: list[str]) -> list[str]:
    """Filtre une liste de noms de colonnes selon les motifs de données personnelles.

    Fonction pure, testée sans dépendance à une base réelle.

    Args:
        noms_colonnes: noms de colonnes à vérifier.

    Returns:
        Le sous-ensemble des noms qui correspondent à un motif suspect.
    """
    return [
        nom for nom in noms_colonnes
        if any(re.search(motif, nom, re.IGNORECASE) for motif in MOTIFS_SUSPECTS)
    ]


def auditer(dsn: str = OMEGA_BI_DB_DSN) -> dict[str, list[str]]:
    """Audite toutes les colonnes de l'entrepôt à la recherche de données personnelles.

    Args:
        dsn: chaîne de connexion vers l'entrepôt.

    Returns:
        Un dict `{"schema.table": [colonnes suspectes]}` — vide si aucune
        colonne suspecte n'est trouvée dans aucune table/vue.
    """
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_schema, table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = ANY(%s)
                ORDER BY table_schema, table_name, ordinal_position
                """,
                (list(SCHEMAS_AUDITES),),
            )
            par_table: dict[str, list[str]] = {}
            for schema, table, colonne in cur.fetchall():
                par_table.setdefault(f"{schema}.{table}", []).append(colonne)
    finally:
        conn.close()

    resultat = {}
    for table, colonnes in par_table.items():
        suspectes = colonnes_suspectes(colonnes)
        if suspectes:
            resultat[table] = suspectes
    return resultat


if __name__ == "__main__":
    trouvees = auditer()
    if trouvees:
        print("ALERTE -- colonnes évoquant une donnée personnelle détectées :")
        for table, colonnes in trouvees.items():
            print(f"  {table}: {', '.join(colonnes)}")
        raise SystemExit(1)
    print("Aucune colonne évoquant une donnée personnelle détectée dans l'entrepôt.")
