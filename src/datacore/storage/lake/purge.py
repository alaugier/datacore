"""Purge RGPD des partitions `raw/` de géolocalisation au-delà de la durée de conservation (C21).

Cible uniquement `geoloc_flotte` et `flux_sse_capteurs` — les 2 flux
identifiés comme portant de la géolocalisation de flotte (voir
`docs/architecture/registre_rgpd_lake.md` §2). Les 3 autres flux
(`capteurs_temperature`, `camera_comptage`, `rfid_scans`) ne sont pas
concernés : aucune obligation de purge RGPD ne s'y applique.

Durée de conservation par défaut : 90 jours, cohérente avec l'engagement
déjà pris en C3 (`architecture_cible.md` §4.2 : « purge automatisée
au-delà d'un horizon défini, ex. 90 jours pour la géolocalisation
brute »).

`staging/`/`curated/` sont reconstruits après la purge pour les flux
concernés (zones régénérables, voir `transform.py`) — sinon la donnée
supprimée de `raw/` resterait visible dans les zones dérivées jusqu'à la
prochaine exécution normale du pipeline, ce qui viderait la purge de son
sens.
"""
import datetime

from datacore.config import OMEGA_LAKE_BUCKET
from datacore.storage.lake.transform import construire_curated, construire_staging

FLUX_GEOLOCALISATION = ("geoloc_flotte", "flux_sse_capteurs")
RETENTION_JOURS = 90


def partitions_a_purger(
    s3,
    flux: str,
    bucket: str = OMEGA_LAKE_BUCKET,
    horizon_jours: int = RETENTION_JOURS,
    aujourdhui: datetime.date | None = None,
) -> list[str]:
    """Liste les clés S3 sous `raw/<flux>/date=.../` plus anciennes que l'horizon de rétention.

    Args:
        s3: client S3.
        flux: nom du flux (un de `FLUX_GEOLOCALISATION`).
        bucket: bucket cible.
        horizon_jours: durée de conservation, en jours.
        aujourdhui: date de référence (paramétrable pour les tests,
            évite une dépendance à la date réelle d'exécution).

    Returns:
        Les clés S3 dont la partition `date=` est strictement antérieure
        à `aujourdhui - horizon_jours`.
    """
    aujourdhui = aujourdhui or datetime.date.today()
    limite = aujourdhui - datetime.timedelta(days=horizon_jours)

    objets = s3.list_objects_v2(Bucket=bucket, Prefix=f"raw/{flux}/").get("Contents", [])
    a_purger = []
    for objet in objets:
        segment_date = objet["Key"].split("/")[2]  # "date=AAAA-MM-JJ"
        date_partition = datetime.date.fromisoformat(segment_date.removeprefix("date="))
        if date_partition < limite:
            a_purger.append(objet["Key"])
    return a_purger


def purger_geolocalisation(
    s3,
    con,
    bucket: str = OMEGA_LAKE_BUCKET,
    horizon_jours: int = RETENTION_JOURS,
    aujourdhui: datetime.date | None = None,
) -> dict[str, list[str]]:
    """Purge les partitions `raw/` de géolocalisation au-delà de la rétention.

    Reconstruit ensuite `staging/`/`curated/` pour les flux concernés,
    sauf si plus aucune partition `raw/` ne subsiste (cas non rencontré
    à ce stade sur le jeu de données réel — `staging/`/`curated/`
    resteraient alors inchangés, limite connue plutôt que gérée).

    Args:
        s3: client S3.
        con: connexion DuckDB ouverte (voir `transform.connexion()`).
        bucket: bucket cible.
        horizon_jours: durée de conservation, en jours.
        aujourdhui: date de référence (paramétrable pour les tests).

    Returns:
        Un dict `{flux: [clés supprimées]}`.
    """
    resultat = {}
    for flux in FLUX_GEOLOCALISATION:
        cles = partitions_a_purger(s3, flux, bucket, horizon_jours, aujourdhui)
        for cle in cles:
            s3.delete_object(Bucket=bucket, Key=cle)
        resultat[flux] = cles

        if cles and s3.list_objects_v2(Bucket=bucket, Prefix=f"raw/{flux}/").get("KeyCount", 0) > 0:
            construire_staging(con, flux, bucket)
            construire_curated(con, flux, bucket)
    return resultat


def main() -> None:
    """Point d'entrée CLI : purge les 2 flux de géolocalisation avec la rétention par défaut."""
    from datacore.storage.lake.ingestion_batch import client
    from datacore.storage.lake.transform import connexion

    resultat = purger_geolocalisation(client(), connexion())
    for flux, cles in resultat.items():
        print(f"{flux} : {len(cles)} partition(s) purgée(s)")


if __name__ == "__main__":
    main()
