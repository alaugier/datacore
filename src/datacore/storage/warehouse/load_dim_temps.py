"""Génère et charge `dimensions.dim_temps` (C14).

Contrairement aux autres dimensions (issues de tables sources FluxPro/
TransFlow, chargées par C15), `Dim_Temps` est une dimension calendaire
générée, sans source de données propre — pratique Kimball standard,
voir `docs/architecture/modelisation_omega_bi.md` §6.4. Ce chargement
fait donc partie de la création de l'entrepôt (C14), pas du pipeline
ETL (C15).

Couvre le 1er janvier 2022 au 31 décembre 2027 : la borne basse couvre
la date la plus ancienne observée dans le jeu de données (2022-01-01,
vérifié empiriquement sur les 4 sources datées), la borne haute laisse
une marge après la date la plus récente (2026-08-08) pour couvrir le
reste du programme (soutenance prévue ~2027-02, voir
`docs/architecture/feuille_de_route.md`).
"""
import datetime

import psycopg2

from datacore.ingestion.config import OMEGA_BI_DB_DSN

DATE_DEBUT = datetime.date(2022, 1, 1)
DATE_FIN = datetime.date(2027, 12, 31)

NOMS_MOIS = [
    "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
]


def generer_lignes(date_debut: datetime.date, date_fin: datetime.date) -> list[tuple]:
    """Génère une ligne `dim_temps` par jour sur `[date_debut, date_fin]`.

    Args:
        date_debut: première date incluse.
        date_fin: dernière date incluse.

    Returns:
        Liste de tuples prêts pour un INSERT, un par jour de la plage.
    """
    lignes = []
    date_courante = date_debut
    un_jour = datetime.timedelta(days=1)
    while date_courante <= date_fin:
        iso_annee, iso_semaine, iso_jour = date_courante.isocalendar()
        lignes.append((
            int(date_courante.strftime("%Y%m%d")),
            date_courante,
            date_courante.year,
            (date_courante.month - 1) // 3 + 1,
            date_courante.month,
            NOMS_MOIS[date_courante.month - 1],
            iso_jour,
            iso_semaine,
            iso_jour >= 6,
        ))
        date_courante += un_jour
    return lignes


def charger_dim_temps(dsn: str = OMEGA_BI_DB_DSN) -> int:
    """Insère les lignes `dim_temps` manquantes dans l'entrepôt.

    Idempotent : `ON CONFLICT DO NOTHING` sur `date_key`, rejouable sans
    dupliquer les lignes déjà présentes.

    Args:
        dsn: chaîne de connexion vers la base OMEGA BI.

    Returns:
        Le nombre de lignes envoyées (avant déduplication par la base).
    """
    lignes = generer_lignes(DATE_DEBUT, DATE_FIN)
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO dimensions.dim_temps
                (date_key, date_complete, annee, trimestre, mois, nom_mois,
                 jour_semaine, numero_semaine, est_weekend)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date_key) DO NOTHING
            """,
            lignes,
        )
        conn.commit()
    return len(lignes)


if __name__ == "__main__":
    n = charger_dim_temps()
    print(f"{n} lignes dim_temps envoyées ({DATE_DEBUT} -> {DATE_FIN}).")
