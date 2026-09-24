"""Export `curated_bi/` — vue filtrée du lake exposée à `lake_reader` (C21bis).

Suite à la revue externe du registre RGPD (C21) : `vehicule_id` dans
`geoloc_flotte`/`flux_sse_capteurs` se recoupe réellement avec
`tournees.chauffeur` (voir `registre_rgpd_lake.md` §2). Trois décisions
actées ici, sur recommandation de la relecture externe :

1. **Pseudonymisation HMAC, pas un hash simple.** Un hash sans clé
   (`sha256(vehicule_id)`) n'apporterait aucune protection : ce jeu de
   données ne compte que 15 véhicules (`VH-001` à `VH-015`) — n'importe
   qui pourrait recalculer les 15 empreintes possibles et retrouver la
   correspondance sans jamais voir la vraie donnée. Une clé secrète
   (`LAKE_PSEUDONYM_KEY`, jamais distribuée à `lake_reader`) rend ce
   recalcul impossible sans elle.

2. **`curated/` n'est jamais modifiée.** Les Data Engineers ont un
   besoin légitime de `vehicule_id` en clair (jointure opérationnelle
   vers `tournees`) — `curated_bi/` est un **export distinct**, dérivé
   de `curated/`, pas une 4e zone du pipeline `raw/`→`staging/`→`curated/`
   décrit dans `architecture_omega_lake.md`.

3. **L'accès de `lake_reader` doit être restreint à ce seul préfixe** —
   vérifié avant cette correction que `lake_reader` pouvait lire
   `raw/`/`staging/`/`curated/` en clair (la politique MinIO d'origine,
   C21, portait sur le bucket entier). Politique corrigée dans
   `infra/minio/lake-reader-policy.json`.

**Limite connue et assumée, hors périmètre de correction ici** : même
`vehicule_id` pseudonymisé, une série temporelle de géolocalisation
dense (1 point/2s, `lat`/`lon`) reste en général ré-identifiante par
motif de déplacement (domicile, horaires réguliers) — connu dans la
littérature sur les données de mobilité. La pseudonymisation réduit le
risque de jointure directe, elle ne l'élimine pas entièrement.

**Garde-fou sur la clé (ajouté après une seconde relecture externe)** :
`config.py` ne fournit plus de valeur de repli pour
`LAKE_PSEUDONYM_KEY` — un repli codé en dur pour un secret
cryptographique est visible dans le dépôt public, donc pas un secret du
tout. `verifier_cle_configuree()` refuse explicitement de continuer
(lève `RuntimeError`) si la clé est absente, vaut une valeur publique
connue (l'exemple de `.env.example` ou l'ancien repli codé en dur,
retiré de ce fichier mais toujours visible dans l'historique git), ou
si elle est trop courte pour offrir une vraie protection HMAC — un
démarrage silencieux avec l'une de ces valeurs romprait la
pseudonymisation sans avertissement.

**Ce que ce garde-fou ne fait pas** : il ne mesure pas l'entropie réelle
de la clé (une chaîne de 32 caractères identiques passerait le contrôle
de longueur). Ce n'est pas un vérificateur de force de mot de passe
générique, juste une garde bon marché contre les erreurs les plus
plausibles (oubli, valeur d'exemple non changée, clé manifestement trop
courte pour un usage HMAC) — proportionné à ce que demande ce projet,
pas une validation cryptographique exhaustive.
"""
import hashlib
import hmac

from datacore.config import LAKE_PSEUDONYM_KEY, OMEGA_LAKE_BUCKET
from datacore.storage.lake.transform import FLUX

FLUX_A_PSEUDONYMISER = ("geoloc_flotte", "flux_sse_capteurs")

# Doit rester identique à la valeur d'exemple de .env.example -- un test
# dédié (test_curated_bi.py) vérifie cette synchronisation.
VALEUR_EXEMPLE_ENV = "changez-moi-avec-une-vraie-cle-aleatoire"

# L'ancien repli codé en dur de config.py, retiré (voir la correction
# précédente) -- toujours rejeté explicitement, au cas où quelqu'un la
# réutiliserait par habitude (copiée depuis un ancien commit, une
# ancienne doc, ou cette conversation elle-même).
ANCIENNE_VALEUR_REPLI_SUPPRIMEE = "datacore_pseudonym_key_dev_only"

# secrets.token_hex(32) (la commande recommandée dans .env.example)
# produit 64 caractères -- 32 est un plancher large en dessous duquel
# une clé est manifestement trop courte pour un usage HMAC sérieux,
# pas une mesure d'entropie réelle (voir note ci-dessus).
LONGUEUR_MINIMALE = 32


def verifier_cle_configuree(cle: str | None) -> str:
    """Refuse explicitement de continuer si la clé est absente, publique connue, ou trop courte.

    Args:
        cle: la valeur de `LAKE_PSEUDONYM_KEY` à vérifier.

    Returns:
        La clé, inchangée, si elle est valide.

    Raises:
        RuntimeError: si la clé est absente/vide, vaut une valeur
            publique connue (exemple de `.env.example` ou ancien repli
            codé en dur), ou fait moins de `LONGUEUR_MINIMALE`
            caractères -- un démarrage silencieux avec l'une de ces
            valeurs romprait la protection HMAC sans avertissement.
    """
    if not cle:
        raise RuntimeError(
            "LAKE_PSEUDONYM_KEY n'est pas définie. Copier .env.example en .env et "
            'générer une vraie valeur aléatoire (`python3 -c "import secrets; '
            'print(secrets.token_hex(32))"`) avant de construire curated_bi/.'
        )
    if cle in (VALEUR_EXEMPLE_ENV, ANCIENNE_VALEUR_REPLI_SUPPRIMEE):
        raise RuntimeError(
            "LAKE_PSEUDONYM_KEY vaut une valeur publique connue (l'exemple de "
            ".env.example, ou l'ancien repli codé en dur -- toutes deux visibles dans "
            "le dépôt). Générer une vraie clé aléatoire avant de construire curated_bi/."
        )
    if len(cle) < LONGUEUR_MINIMALE:
        raise RuntimeError(
            f"LAKE_PSEUDONYM_KEY est trop courte ({len(cle)} caractères, "
            f"{LONGUEUR_MINIMALE} minimum) pour offrir une vraie protection HMAC. "
            'Générer une vraie valeur aléatoire (`python3 -c "import secrets; '
            'print(secrets.token_hex(32))"`) avant de construire curated_bi/.'
        )
    return cle


def pseudonyme(vehicule_id: str, cle: str | None = LAKE_PSEUDONYM_KEY) -> str:
    """Calcule le pseudonyme HMAC-SHA256 stable d'un identifiant véhicule.

    Args:
        vehicule_id: identifiant réel (ex. `"VH-004"`).
        cle: clé secrète HMAC (jamais distribuée à `lake_reader`).

    Returns:
        Un pseudonyme hexadécimal (16 caractères) stable — le même
        `vehicule_id` produit toujours le même pseudonyme (continuité
        analytique préservée d'une exécution à l'autre), mais
        impossible à recalculer sans la clé.

    Raises:
        RuntimeError: voir `verifier_cle_configuree()` -- appelée
            systématiquement ici, pas seulement aux points d'entrée du
            pipeline, pour qu'aucun appel (test compris) ne puisse
            contourner le garde-fou.
    """
    cle = verifier_cle_configuree(cle)
    return hmac.new(cle.encode(), vehicule_id.encode(), hashlib.sha256).hexdigest()[:16]


def construire_curated_bi(con, flux: str, bucket: str = OMEGA_LAKE_BUCKET) -> str:
    """Reconstruit `curated_bi/<flux>/part-0.parquet` depuis `curated/<flux>/`.

    Copie telle quelle pour les flux sans donnée de géolocalisation ;
    pour `geoloc_flotte`/`flux_sse_capteurs`, remplace `vehicule_id` par
    son pseudonyme HMAC.

    Args:
        con: connexion DuckDB ouverte (voir `transform.connexion()`).
        flux: nom du flux à traiter.
        bucket: bucket cible.

    Returns:
        La clé S3 du fichier écrit.
    """
    cle_sortie = f"curated_bi/{flux}/part-0.parquet"
    source = f"read_parquet('s3://{bucket}/curated/{flux}/part-0.parquet')"

    if flux not in FLUX_A_PSEUDONYMISER:
        con.sql(f"COPY (SELECT * FROM {source}) TO 's3://{bucket}/{cle_sortie}' (FORMAT PARQUET)")
        return cle_sortie

    identifiants = con.sql(f"SELECT DISTINCT vehicule_id FROM {source}").fetchall()
    correspondance = [(vehicule_id, pseudonyme(vehicule_id)) for (vehicule_id,) in identifiants]

    con.sql("DROP TABLE IF EXISTS _correspondance_pseudonyme")
    con.sql(
        "CREATE TEMP TABLE _correspondance_pseudonyme "
        "(vehicule_id VARCHAR, pseudonyme VARCHAR)"
    )
    con.executemany(
        "INSERT INTO _correspondance_pseudonyme VALUES (?, ?)", correspondance
    )

    con.sql(f"""
        COPY (
            SELECT s.* EXCLUDE (vehicule_id), c.pseudonyme AS vehicule_id
            FROM {source} s
            JOIN _correspondance_pseudonyme c ON c.vehicule_id = s.vehicule_id
        ) TO 's3://{bucket}/{cle_sortie}' (FORMAT PARQUET)
    """)
    con.sql("DROP TABLE _correspondance_pseudonyme")
    return cle_sortie


def construire_curated_bi_complet(con, bucket: str = OMEGA_LAKE_BUCKET) -> dict[str, str]:
    """Reconstruit `curated_bi/` pour les 5 flux.

    Args:
        con: connexion DuckDB ouverte.
        bucket: bucket cible.

    Returns:
        Un dict `{flux: clé S3 écrite}`.
    """
    return {flux: construire_curated_bi(con, flux, bucket) for flux in FLUX}


def main() -> None:
    """Point d'entrée CLI : reconstruit `curated_bi/` pour les 5 flux."""
    from datacore.storage.lake.transform import connexion

    for flux, cle in construire_curated_bi_complet(connexion()).items():
        print(f"{flux}: {cle}")


if __name__ == "__main__":
    main()
