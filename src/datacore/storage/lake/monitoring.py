"""Monitoring du data lake OMEGA LAKE — conditions applicatives et matérielles (C20bis).

Le référentiel de compétences est explicite sur C20 : *« Le monitorage
permet le suivi des conditions matérielles et applicatives. Le
monitorage génère une alerte lors d'une rupture de service. »* (voir
`docs/reference/Referentiel_Activites_Competences_Evaluation_DE.pdf`,
page 24). Ce module couvre le premier volet (suivi) ; l'alerte
elle-même est configurée côté Grafana (règle d'alerte + webhook, voir
`docs/architecture/gestion_operationnelle_omega_bi.md`).

Trois relevés, chacun en ajout seul (append-only) dans le schéma
Postgres `monitoring` (même base que l'entrepôt OMEGA BI, sobriété
RGESN) pour que Grafana puisse tracer une évolution, pas seulement un
dernier état :

- **Applicatif** : `enregistrer_catalogue()` (fraîcheur/volumétrie par
  flux/zone, réutilise `catalogue.construire_catalogue()`) et
  `enregistrer_purge()` (dernière purge RGPD exécutée).
- **Matériel** : `verifier_sante_infrastructure()` (MinIO accessible,
  capacité utilisée) — c'est le volet que le premier design de C20bis
  ne couvrait pas, corrigé après relecture du référentiel.
"""
import datetime

import psycopg2

from datacore.config import OMEGA_BI_DB_DSN, OMEGA_LAKE_BUCKET
from datacore.storage.lake.catalogue import construire_catalogue


def enregistrer_catalogue(
    con_lake, s3, dsn: str = OMEGA_BI_DB_DSN, bucket: str = OMEGA_LAKE_BUCKET
) -> int:
    """Relève le catalogue courant du lake et l'enregistre dans `monitoring.catalogue_lake`.

    Args:
        con_lake: connexion DuckDB ouverte (voir `transform.connexion()`).
        s3: client S3 (boto3).
        dsn: chaîne de connexion vers l'entrepôt (schéma `monitoring`).
        bucket: bucket cible.

    Returns:
        Le nombre d'entrées de catalogue enregistrées.
    """
    catalogue = construire_catalogue(con_lake, s3, bucket)
    releve_le = datetime.datetime.now()

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO monitoring.catalogue_lake
                (flux, zone, nb_lignes, derniere_modification, releve_le)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                (e["flux"], e["zone"], e["nb_lignes"], e["derniere_modification"], releve_le)
                for e in catalogue
            ],
        )
    return len(catalogue)


def enregistrer_purge(resultat_purge: dict[str, list[str]], dsn: str = OMEGA_BI_DB_DSN) -> None:
    """Enregistre le résultat d'une exécution de purge dans `monitoring.purges_lake`.

    Args:
        resultat_purge: le dict `{flux: [clés supprimées]}` renvoyé par
            `purge.purger_geolocalisation()`.
        dsn: chaîne de connexion vers l'entrepôt.
    """
    execute_le = datetime.datetime.now()
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO monitoring.purges_lake (flux, nb_partitions_purgees, execute_le)
            VALUES (%s, %s, %s)
            """,
            [(flux, len(cles), execute_le) for flux, cles in resultat_purge.items()],
        )


def verifier_sante_infrastructure(
    s3, dsn: str = OMEGA_BI_DB_DSN, bucket: str = OMEGA_LAKE_BUCKET
) -> dict:
    """Vérifie l'accessibilité de MinIO et relève la capacité utilisée (volet matériel, C20bis).

    N'échoue jamais si MinIO est injoignable : c'est justement l'état à
    détecter et enregistrer, pas une erreur du monitoring lui-même.

    Args:
        s3: client S3 (boto3).
        dsn: chaîne de connexion vers l'entrepôt.
        bucket: bucket cible.

    Returns:
        `{"minio_accessible": bool, "capacite_utilisee_octets": int | None}`.
    """
    try:
        paginator = s3.get_paginator("list_objects_v2")
        capacite = sum(
            objet["Size"]
            for page in paginator.paginate(Bucket=bucket)
            for objet in page.get("Contents", [])
        )
        accessible = True
    except Exception:
        accessible = False
        capacite = None

    releve_le = datetime.datetime.now()
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO monitoring.sante_infrastructure
                (minio_accessible, capacite_utilisee_octets, releve_le)
            VALUES (%s, %s, %s)
            """,
            (accessible, capacite, releve_le),
        )
    return {"minio_accessible": accessible, "capacite_utilisee_octets": capacite}


def main() -> None:
    """Point d'entrée CLI : exécute les 3 relevés (catalogue, purge non incluse, santé)."""
    from datacore.storage.lake.ingestion_batch import client
    from datacore.storage.lake.transform import connexion

    s3 = client()
    con = connexion()

    nb_entrees = enregistrer_catalogue(con, s3)
    print(f"catalogue : {nb_entrees} entrée(s) enregistrée(s)")

    sante = verifier_sante_infrastructure(s3)
    print(f"santé infrastructure : {sante}")


if __name__ == "__main__":
    main()
