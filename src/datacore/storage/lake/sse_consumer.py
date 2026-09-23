"""Consommateur du flux SSE `/api/stream/capteurs` vers raw/ (C19).

Nommage : le flux déposé sous `raw/flux_sse_capteurs/` est un flux
**distinct** de `capteurs_temperature` (fichier batch CSV) malgré le nom
proche -- le flux SSE combine température et géolocalisation dans le
même évènement (voir `architecture_omega_lake.md` §1), le batch CSV ne
porte que la température. Ne pas les confondre.

Robustesse : le flux source **n'est pas rejouable**
(`topographie_donnees.md` §3.5, "pas de rejeu possible, flux non
historisé côté source") -- une coupure du consommateur perd
irrémédiablement les évènements manqués pendant la coupure elle-même,
aucun mécanisme de rattrapage n'existe côté serveur. La stratégie de
robustesse porte donc sur ce qui *est* sous contrôle : ne jamais laisser
le tampon local grossir plus que ce qu'on est prêt à perdre. Chaque
évènement est mis en tampon dès sa réception, et le tampon est déversé
(upload S3, un nouveau fichier "part") dès qu'un `intervalle` s'est
écoulé depuis le dernier dépôt -- pas seulement à la fin de la journée.
En cas de coupure, la perte réelle est bornée à `intervalle`, jamais à
toute une journée. Comportement vérifié en pratique (coupure brutale
simulée, pas seulement décrite) dans
`notebooks/verification_sse_consumer.ipynb`.
"""
import datetime
import json
import time
from collections.abc import Iterable, Iterator
from typing import Any

import requests

from datacore.config import (
    OMEGA_LAKE_BUCKET,
    TRANSFLOW_API_KEY,
    TRANSFLOW_API_URL,
)
from datacore.storage.lake.ingestion_batch import client

FLUX = "flux_sse_capteurs"
INTERVALLE_PAR_DEFAUT = datetime.timedelta(minutes=5)


def evenements_depuis_lignes(lignes: Iterable[bytes | str]) -> Iterator[dict[str, Any]]:
    """Décode les évènements JSON portés par un flux SSE brut.

    Args:
        lignes: itérable de lignes brutes (réel : `response.iter_lines()`
            d'une requête `stream=True` ; test : liste/itérateur fabriqué).
            Ignore les lignes vides et les commentaires SSE (heartbeat) --
            seules les lignes `data: {...}` portent un évènement.

    Yields:
        Le dict JSON décodé de chaque évènement.
    """
    for ligne in lignes:
        if isinstance(ligne, bytes):
            ligne = ligne.decode("utf-8")
        if not ligne.startswith("data: "):
            continue
        yield json.loads(ligne[len("data: ") :])


def _deverser(
    evenements: list[dict[str, Any]], s3, bucket: str, horodatage: datetime.datetime
) -> str:
    """Dépose un tampon d'évènements en un fichier NDJSON sous raw/.

    Args:
        evenements: évènements accumulés depuis le dernier dépôt.
        s3: client S3.
        bucket: bucket cible.
        horodatage: heure du dépôt (détermine la partition `date=` et
            le nom de fichier, unique par microseconde -- deux dépôts
            successifs ne peuvent pas se marcher dessus).

    Returns:
        La clé S3 de l'objet déposé.
    """
    contenu = "\n".join(json.dumps(e, ensure_ascii=False) for e in evenements)
    jour = horodatage.date().isoformat()
    nom_fichier = f"part-{horodatage.strftime('%H%M%S%f')}.ndjson"
    cle = f"raw/{FLUX}/date={jour}/{nom_fichier}"
    s3.put_object(Bucket=bucket, Key=cle, Body=contenu.encode("utf-8"))
    return cle


def consommer(
    lignes: Iterable[bytes | str],
    s3,
    bucket: str = OMEGA_LAKE_BUCKET,
    intervalle: datetime.timedelta = INTERVALLE_PAR_DEFAUT,
    horloge=datetime.datetime.now,
    duree_max: datetime.timedelta | None = None,
) -> list[str]:
    """Consomme un flux SSE et dépose des fichiers NDJSON par fenêtre dans raw/.

    Args:
        lignes: itérable de lignes SSE brutes.
        s3: client S3 (boto3 en production, factice en test).
        bucket: bucket cible.
        intervalle: durée entre deux dépôts (perte maximale en cas de
            coupure -- voir le docstring du module).
        horloge: fonction sans argument renvoyant l'heure courante,
            injectable pour les tests (évite un vrai `time.sleep`).
        duree_max: arrête la consommation après cette durée écoulée
            (utilisé en test/démonstration ; `None` = tourne jusqu'à
            épuisement du flux, cas réel avec un flux non borné).

    Returns:
        La liste des clés S3 déposées, dans l'ordre.
    """
    debut = horloge()
    dernier_depot = debut
    tampon: list[dict[str, Any]] = []
    cles: list[str] = []

    for evenement in evenements_depuis_lignes(lignes):
        tampon.append(evenement)
        maintenant = horloge()
        if maintenant - dernier_depot >= intervalle:
            cles.append(_deverser(tampon, s3, bucket, maintenant))
            tampon = []
            dernier_depot = maintenant
        if duree_max is not None and maintenant - debut >= duree_max:
            break

    if tampon:
        cles.append(_deverser(tampon, s3, bucket, horloge()))

    return cles


def main() -> None:
    """Point d'entrée CLI : consomme le flux réel jusqu'à interruption (Ctrl+C/SIGKILL).

    Reconnexion automatique sur coupure réseau transitoire (la requête
    lève une exception mais le processus reste vivant) -- distinct d'un
    arrêt complet du processus (SIGKILL, crash), qui n'est pas géré ici :
    relancer le processus entier ne perd que l'intervalle en cours, voir
    le docstring du module. Ce processus est longue durée et non borné ;
    son orchestration en production (relance automatique si le processus
    lui-même s'arrête) est hors périmètre de ce livrable.
    """
    url = f"{TRANSFLOW_API_URL}/api/stream/capteurs"
    while True:
        try:
            with requests.get(
                url, headers={"X-API-Key": TRANSFLOW_API_KEY}, stream=True, timeout=None
            ) as reponse:
                reponse.raise_for_status()
                cles = consommer(reponse.iter_lines(), client())
                print(f"{len(cles)} fichiers déposés dans {OMEGA_LAKE_BUCKET}/raw/{FLUX}/")
        except requests.RequestException as exc:
            print(f"Connexion au flux perdue ({exc}), reconnexion dans 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()
