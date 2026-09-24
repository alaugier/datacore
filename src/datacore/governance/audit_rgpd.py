#!/usr/bin/env python3
"""Audit RGPD de l'entrepôt OMEGA BI (C16) et du data lake OMEGA LAKE (C21).

Vérifie par introspection du schéma réel qu'aucune colonne évoquant une
donnée personnelle n'a été introduite — un contrôle répétable à chaque
revue, pas une conclusion figée une fois pour toutes dans la
documentation. `colonnes_suspectes()` est réutilisée telle quelle pour
les deux cibles (mêmes motifs, même détection lexicale) ; seule la
source du schéma change : `information_schema.columns` pour l'entrepôt
(SQL), le catalogue généré par `datacore.storage.lake.catalogue` pour le
lake (pas de schéma SQL central pour du Parquet dans un stockage objet).
Voir `docs/architecture/registre_rgpd_entrepot.md` (C16) et
`docs/architecture/registre_rgpd_lake.md` (C21) pour l'analyse complète.

**Limite connue de la détection lexicale, pour le lake** : le risque de
ré-identification par jointure (`vehicule_id` → `tournees.chauffeur`,
voir `architecture_omega_lake.md` §6) n'est pas un nom de colonne
suspect en lui-même — traité par une décision de conception (pas de
jointure automatisée), pas par ce contrôle. Ce script détecte les
colonnes personnelles *directement nommées*, pas les risques structurels
de recoupement entre jeux de données.

Lancement :
    python3 -m datacore.governance.audit_rgpd
"""
import re

import psycopg2

from datacore.config import OMEGA_BI_DB_DSN, OMEGA_LAKE_BUCKET

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


def auditer_lake(con, s3, bucket: str = OMEGA_LAKE_BUCKET) -> dict[str, list[str]]:
    """Audite le schéma réel du data lake (catalogue C20) à la recherche de données personnelles.

    Args:
        con: connexion DuckDB ouverte (voir `storage.lake.transform.connexion()`).
        s3: client S3 (voir `storage.lake.ingestion_batch.client()`).
        bucket: bucket cible.

    Returns:
        Un dict `{"zone/flux": [colonnes suspectes]}` — vide si aucune
        colonne suspecte n'est trouvée dans aucun flux/zone du lake.
    """
    from datacore.storage.lake.catalogue import construire_catalogue

    resultat = {}
    for entree in construire_catalogue(con, s3, bucket):
        noms = [colonne["colonne"] for colonne in entree["schema"]]
        suspectes = colonnes_suspectes(noms)
        if suspectes:
            resultat[f"{entree['zone']}/{entree['flux']}"] = suspectes
    return resultat


if __name__ == "__main__":
    from datacore.storage.lake.ingestion_batch import client as client_s3
    from datacore.storage.lake.transform import connexion as connexion_lake

    en_alerte = False

    trouvees_entrepot = auditer()
    if trouvees_entrepot:
        en_alerte = True
        print("ALERTE -- colonnes évoquant une donnée personnelle détectées (entrepôt) :")
        for table, colonnes in trouvees_entrepot.items():
            print(f"  {table}: {', '.join(colonnes)}")
    else:
        print("Entrepôt OMEGA BI : aucune colonne évoquant une donnée personnelle détectée.")

    trouvees_lake = auditer_lake(connexion_lake(), client_s3())
    if trouvees_lake:
        en_alerte = True
        print("ALERTE -- colonnes évoquant une donnée personnelle détectées (data lake) :")
        for cle, colonnes in trouvees_lake.items():
            print(f"  {cle}: {', '.join(colonnes)}")
    else:
        print("Data lake OMEGA LAKE : aucune colonne évoquant une donnée personnelle détectée.")

    if en_alerte:
        raise SystemExit(1)
