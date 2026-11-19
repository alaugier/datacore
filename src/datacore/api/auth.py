"""Authentification par JWT pour l'Omega Data API (C12).

Depuis le 19/11/2026 (voir
`docs/architecture/evolution_authentification_jwt.md`) : une clé API
(`config.API_KEYS`) n'est plus envoyée directement sur chaque requête --
elle est échangée une fois contre un jeton signé via `POST /auth/token`
(`principal_pour_cle` + `creer_token`), puis le jeton est vérifié
localement (signature + expiration, `get_current_principal`) sur
chaque requête suivante, sans relire le registre de clés. C'est tout
l'apport du JWT par rapport à la clé API directe : la vérification
devient un calcul cryptographique local, pas un lookup -- un vrai gain
seulement une fois ce registre déplacé vers une base partagée entre
plusieurs services (voir l'annexe sécurité de la soutenance, page 69).

Deux dépendances FastAPI, inchangées dans leur usage par `main.py` :
`get_current_principal` (authentification seule) et `require_internal`
(autorisation — réservé aux rôles internes, exclut les référents
clients externes).
"""
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from datacore.api.config import (
    API_KEYS,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    Principal,
    Role,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class CleAPIForm:
    """Formulaire d'échange clé API -> JWT pour `POST /auth/token`.

    Mêmes noms de champ que `fastapi.security.OAuth2PasswordRequestForm`
    (compatible avec le bouton "Authorize" de Swagger, qui envoie
    toujours `username`/`password`), mais `password` y est réellement
    optionnel : `OAuth2PasswordRequestForm` le déclare `Form(...)`
    (obligatoire et non vide), ce qui rejette une soumission avec un
    mot de passe laissé vide (422) -- vérifié empiriquement en écrivant
    les tests de ce module, pas supposé. Ce programme n'a pas de mot de
    passe séparé de la clé API (`username`), donc `password` n'est
    jamais lu ni vérifié ici.
    """

    def __init__(self, username: str = Form(...), password: str = Form(default="")):
        self.username = username
        self.password = password


def principal_pour_cle(api_key: str) -> Principal:
    """Résout une clé API en `Principal` -- utilisé uniquement par `POST /auth/token`.

    La clé API n'est plus envoyée sur les requêtes suivantes, seul le
    jeton émis ici l'est (voir `creer_token`).

    Args:
        api_key: la clé API fournie (champ `username` du formulaire
            OAuth2 -- voir le commentaire sur l'endpoint `/auth/token`).

    Returns:
        Le `Principal` correspondant à la clé.

    Raises:
        HTTPException: 401 si la clé est inconnue.
    """
    principal = API_KEYS.get(api_key)
    if principal is None:
        raise HTTPException(status_code=401, detail="Clé API invalide")
    return principal


def creer_token(principal: Principal) -> str:
    """Émet un JWT signé portant le rôle et le périmètre client, avec expiration.

    Args:
        principal: identité déjà résolue (voir `principal_pour_cle`).

    Returns:
        Le jeton encodé (python-jose, `JWT_ALGORITHM`).
    """
    expire = datetime.now(UTC) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "role": principal.role.value,
        "client": principal.client,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_principal(token: str = Depends(oauth2_scheme)) -> Principal:
    """Résout le jeton JWT reçu (en-tête `Authorization: Bearer ...`) en `Principal`.

    Vérification locale uniquement (signature + expiration) : ne relit
    jamais `config.API_KEYS`.

    Args:
        token: jeton extrait par `OAuth2PasswordBearer`.

    Returns:
        Le `Principal` correspondant au jeton.

    Raises:
        HTTPException: 401 si le jeton est absent, invalide ou expiré.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expiré") from None
    role_brut = payload.get("role")
    if role_brut is None:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expiré")
    return Principal(role=Role(role_brut), client=payload.get("client"))


def require_internal(principal: Principal = Depends(get_current_principal)) -> Principal:
    """Exige un rôle interne (Data Engineer ou Data Analyst).

    Args:
        principal: identité déjà résolue par `get_current_principal`.

    Returns:
        Le `Principal`, si son rôle est autorisé.

    Raises:
        HTTPException: 403 si l'appelant est un référent client externe.
    """
    if principal.role == Role.CLIENT_REFERENT:
        raise HTTPException(
            status_code=403, detail="Réservé aux équipes internes (Data Engineers/Analysts)"
        )
    return principal
