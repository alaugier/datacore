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
- **Débit du flux SSE temps réel** : `enregistrer_evenements_fenetre()`
  (nombre d'évènements reçus par fenêtre de dépôt, appelé par
  `sse_consumer.main()`) — avant cette fonction, seule la fraîcheur
  globale du flux était suivie, pas son débit réel (issue #104).
- **Scraping du portail transporteur** : `enregistrer_scraping_portail()`
  (nombre de colis, erreurs HTTP, durée, appelé par
  `run_extraction.extract_portail()`) — n'est pas un livrable du
  périmètre C20/C20bis (le scraping relève du Bloc 2, C8), ajouté par
  pragmatisme pour le rendre visible dans Grafana : le journal d'audit
  (`gouvernance.journal_operations`) n'y est pas accessible, voir le
  docstring de la fonction (issue #104).
"""
import datetime

import psycopg2

from datacore.config import OMEGA_BI_DB_DSN, OMEGA_LAKE_BUCKET
from datacore.storage.lake.catalogue import construire_catalogue


def _maintenant_utc() -> datetime.datetime:
    """Horodatage naïf en UTC (issue #104).

    Les colonnes `releve_le`/`execute_le` du schéma `monitoring` sont des
    `TIMESTAMP` Postgres sans fuseau horaire. Les panels Grafana qui les
    filtrent par plage temporelle (macro `$__timeFilter`) comparent en
    UTC -- un horodatage en heure locale (`datetime.datetime.now()`, CET
    = UTC+1 en hiver) se retrouve alors perçu comme "dans le futur" par
    rapport au `now` UTC de Grafana, et le panel affiche "No data" malgré
    des lignes réellement présentes (constaté en conditions réelles sur
    `monitoring.debit_flux_sse`, pas une hypothèse).
    """
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


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
    releve_le = _maintenant_utc()

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
    execute_le = _maintenant_utc()
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO monitoring.purges_lake (flux, nb_partitions_purgees, execute_le)
            VALUES (%s, %s, %s)
            """,
            [(flux, len(cles), execute_le) for flux, cles in resultat_purge.items()],
        )


def enregistrer_evenements_fenetre(
    flux: str, nb_evenements: int, releve_le: datetime.datetime, dsn: str = OMEGA_BI_DB_DSN
) -> None:
    """Enregistre le débit d'une fenêtre du flux SSE dans `monitoring.debit_flux_sse` (issue #104).

    Table dédiée, pas `catalogue_lake` : réutiliser `catalogue_lake`
    (flux/zone/nb_lignes) aurait mélangé deux significations différentes
    sous la même clé (flux, zone) -- le volume cumulé du flux relevé par
    `enregistrer_catalogue()`, et le nombre d'évènements d'une seule
    fenêtre relevé ici. Détecté en vérifiant le dashboard Grafana (le
    panel existant n'affiche que la dernière ligne par flux/zone, pas un
    historique), pas en relisant seulement le code. Appelé par
    `sse_consumer.consommer()` via son callback `sur_depot` à chaque
    fenêtre, pas seulement à la fin d'une connexion.

    Args:
        flux: nom du flux (`sse_consumer.FLUX`, toujours
            `"flux_sse_capteurs"` en pratique).
        nb_evenements: nombre d'évènements reçus pendant cette fenêtre.
        releve_le: horodatage du dépôt (même valeur que le nom de fichier
            S3 déposé par `_deverser()`).
        dsn: chaîne de connexion vers l'entrepôt.
    """
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO monitoring.debit_flux_sse (flux, nb_evenements, releve_le)
            VALUES (%s, %s, %s)
            """,
            (flux, nb_evenements, releve_le),
        )


def enregistrer_scraping_portail(
    nb_colis_scrapes: int,
    nb_erreurs_http: int,
    duree_ms: int,
    releve_le: datetime.datetime,
    dsn: str = OMEGA_BI_DB_DSN,
) -> None:
    """Enregistre un relevé du scraping dans `monitoring.scraping_portail` (issue #104).

    Distinct du journal d'audit `gouvernance.journal_operations`
    (`run_extraction.extract_portail()`, réutilise le mécanisme de C16) :
    `bi_reader` (le rôle utilisé par Grafana) n'a délibérément pas accès
    au schéma `gouvernance` (vérifié : `permission denied for schema
    gouvernance`, cohérent avec
    `gestion_operationnelle_omega_bi.md` §3.5/§4 -- "préoccupation
    d'exploitation technique, pas un objet d'analyse métier"). Ce relevé
    duplique le minimum nécessaire à la visualisation Grafana, sans
    donner à `bi_reader` accès à `gouvernance` -- le journal d'audit
    reste la trace de référence, inchangé.

    Args:
        nb_colis_scrapes: nombre de colis scrapés avec succès.
        nb_erreurs_http: nombre d'erreurs HTTP (404 notamment).
        duree_ms: durée de l'exécution en millisecondes.
        releve_le: horodatage de l'exécution.
        dsn: chaîne de connexion vers l'entrepôt.
    """
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO monitoring.scraping_portail
                (nb_colis_scrapes, nb_erreurs_http, duree_ms, releve_le)
            VALUES (%s, %s, %s, %s)
            """,
            (nb_colis_scrapes, nb_erreurs_http, duree_ms, releve_le),
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

    releve_le = _maintenant_utc()
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
