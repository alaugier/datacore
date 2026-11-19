# Évolution de l'authentification : clé API → JWT (C12)

**Compétence couverte : C12 — Partager le jeu de données**
**Date : 19/11/2026, après la soutenance orale (jalon M6)**

## 1. Contexte

Jusqu'au 19/11/2026, l'Omega Data API authentifiait chaque appelant par
une clé API statique envoyée en clair sur chaque requête (en-tête
`X-API-Key`), vérifiée par un simple lookup dans un registre codé en dur
(`src/datacore/api/config.py`, `API_KEYS`). Ce choix était documenté et
assumé — voir l'annexe sécurité du diaporama de soutenance
(`slides/slides.md`, « Clé API : feuille de route sécurité ») — comme
proportionné à l'échelle du programme (3 référents clients, 2 rôles
internes, un parc fixe et connu à l'avance), et conforme au référentiel
RNCP37638 (C12), qui exige une authentification et/ou autorisation
documentées, sans imposer de mécanisme précis.

Cette annexe identifiait néanmoins trois risques réels, non couverts par
une clé statique seule :

1. **Clé devinable** : format prévisible (`omega-<slug>-2026`), pas un
   secret aléatoire.
2. **Pas de révocation sans redéploiement** : retirer l'accès à une clé
   compromise exige de modifier le code.
3. **Pas d'expiration** : une clé compromise reste valable indéfiniment.

## 2. Décision

Implémenté après la soutenance (le jalon M6 ne portait pas cette
fonctionnalité — pas de risque pris sur une démonstration déjà
répétée), avant la date limite de rendu du 20/11/2026. Mécanisme retenu,
conforme au « palier 2 » de l'annexe sécurité :

- **python-jose** (pas PyJWT) — bibliothèque déjà utilisée dans un
  projet personnel antérieur (`healthai_coach_backend`, FastAPI +
  python-jose + `OAuth2PasswordBearer`, même schéma de dépendances
  `Depends()`).
- **`OAuth2PasswordBearer`**, pas `HTTPBearer` — s'intègre nativement au
  bouton « Authorize » de Swagger (vérifié : le champ `username` reçoit
  la clé API, le champ `password` est laissé vide).
- **HS256** (HMAC, clé de signature partagée) — un seul service émetteur
  et vérificateur, pas besoin d'un algorithme asymétrique (RS256)
  réservé au cas où plusieurs services indépendants devraient
  seulement *vérifier* sans jamais émettre.
- **Expiration à 8h** (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480`),
  cohérente avec l'annexe sécurité présentée à l'oral.

### Ce que ce choix ferme, et ce qu'il ne ferme pas

Conforme à ce qui avait été annoncé à l'oral : **JWT seul ne suffit
toujours pas**. Il ferme la devinabilité (le jeton n'est plus un
identifiant prévisible) et l'absence d'expiration. Il ne ferme PAS
l'interception en transit (le jeton, comme l'ancienne clé, voyage en
clair sur HTTP non chiffré — seul TLS le fermerait) ni le brute-force
sur `/auth/token` (aucun rate-limiting mis en place). Ces deux points
restent des limites assumées, cohérentes avec « Limites connues »
(`slides/slides.md`).

## 3. Ce qui change, ce qui ne change pas

**Ne change pas** : les 5 clés API (`config.py`), leur rôle, leur
périmètre client ; toute la logique métier des routes (`main.py`) —
`get_current_principal`/`require_internal` gardent exactement la même
signature, donc aucune route n'a eu à être modifiée ; les réponses des
endpoints (mêmes codes HTTP, mêmes corps JSON).

**Change** : une clé API n'est plus jamais envoyée directement sur une
requête de données. Elle est échangée **une fois**, via
`POST /auth/token` (champ `username` = la clé, `password` ignoré, non
vérifié), contre un jeton JWT. Ce jeton est ensuite envoyé en en-tête
`Authorization: Bearer <jeton>` sur toutes les requêtes suivantes,
vérifié localement (signature + expiration) sans relire le registre de
clés.

## 4. Fichiers modifiés

| Fichier | Changement |
|---|---|
| `src/datacore/api/config.py` | `JWT_SECRET_KEY`/`JWT_ALGORITHM`/`JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (lues depuis l'environnement, jamais codées en dur en valeur réelle) |
| `src/datacore/api/auth.py` | `principal_pour_cle()` + `creer_token()` (émission) ; `get_current_principal()` réécrite pour décoder un JWT au lieu d'un lookup dict ; `CleAPIForm` (formulaire `username`/`password` optionnel — voir §5) |
| `src/datacore/api/main.py` | Nouvel endpoint `POST /auth/token` |
| `src/datacore/api/schemas.py` | Modèle `Token` (`access_token`, `token_type`) |
| `requirements.txt` | `python-jose>=3.3`, `python-multipart>=0.0.9` (requis par FastAPI pour parser un formulaire) |
| `requirements-dev.txt` | `types-python-jose` (stubs mypy) |
| `.env` / `.env.example` | `JWT_SECRET_KEY`/`JWT_ALGORITHM`/`JWT_ACCESS_TOKEN_EXPIRE_MINUTES` |
| `infra/docker/docker-compose.yml` | Variables JWT injectées au service `omega-data-api` |
| `tests/integration/test_api_routes.py` | Toutes les requêtes passent désormais par un jeton (helper `auth_headers()`), 2 tests ajoutés pour `/auth/token` lui-même |
| `notebooks/demo_omega_data_api.ipynb` | `call()` échange la clé contre un jeton en interne ; ré-exécuté pour de vrai, sorties authentiques |
| `docs/architecture/api_omega_data.md` | §2.1 et §5 mis à jour |

## 5. Un détail d'implémentation rencontré en vérifiant

`fastapi.security.OAuth2PasswordRequestForm` (la classe standard de
FastAPI pour ce flux) déclare `password: str = Form(...)` — un champ
**obligatoire et non vide**. Soumettre le formulaire avec un mot de
passe réellement vide (ce que ce programme demande, puisqu'il n'a pas
de mot de passe séparé de la clé) renvoie une erreur 422 — vérifié
empiriquement en écrivant les tests, pas supposé. Remplacé par
`CleAPIForm` (`auth.py`), un formulaire local avec les mêmes noms de
champ (donc toujours compatible avec le bouton « Authorize » de
Swagger, qui envoie toujours `username`/`password`), mais
`password: str = Form(default="")` — réellement optionnel.

## 6. Vérification

Tout ce qui est affirmé ci-dessus a été exécuté réellement, pas
seulement relu :

- `ruff check` : clean.
- `mypy src/datacore/api/` : clean (après installation de
  `types-python-jose`).
- `pytest tests/` : 187 passés (185 + 2 nouveaux tests sur
  `/auth/token`).
- Image Docker `omega-data-api` reconstruite, conteneur sain.
- Flux complet testé contre le conteneur réel : `curl` (émission +
  vérification + 403 de périmètre + 401 sans jeton + 401 clé invalide)
  et l'interface Swagger réelle (bouton « Authorize », champ `username`
  rempli, `password` vide → « Authorized »).
- `notebooks/demo_omega_data_api.ipynb` ré-exécuté de bout en bout
  contre l'instance réelle, sorties capturées authentiques.
