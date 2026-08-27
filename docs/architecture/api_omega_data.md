# Omega Data API — DATA CORE

**Compétence couverte : C12 — Partager le jeu de données**
**Épreuve associée : E4 (mise en situation professionnelle)**

Ce document décrit l'API REST « Omega Data API » (`src/datacore/api/`),
qui expose le jeu de données consolidé produit par les compétences C8 à
C11 (base de travail de staging) aux équipes BI et data science, avec
authentification et autorisation.

---

## 1. Choix technique : FastAPI

Le reste du projet utilise Flask (`api-mock/app.py`, fourni par le
cahier des charges). Pour cette API que nous concevons nous-mêmes, le
choix s'est porté sur **FastAPI** plutôt que Flask :

- le livrable C12 exige explicitement une **spécification OpenAPI
  documentée** — FastAPI la génère automatiquement à partir des
  signatures de fonctions et des modèles Pydantic (`/openapi.json`,
  documentation interactive sur `/docs`), sans maintenance manuelle d'un
  fichier YAML séparé ;
- validation automatique des paramètres de requête et sérialisation des
  réponses par les mêmes modèles Pydantic qui documentent l'API.

Aucun outil n'étant imposé par le référentiel (« Aucun outil précis
n'est imposé »), ce choix reste local à `src/datacore/api/` et ne remet
pas en cause l'usage de Flask ailleurs dans le projet.

---

## 2. Authentification et autorisation

### 2.1 Authentification

Chaque requête (hors `/health`) doit porter l'en-tête `X-API-Key`, sur le
même principe que l'API mock TransFlow fournie. Clés à usage pédagogique
(voir `src/datacore/api/config.py`) :

| Clé | Rôle | Périmètre |
|---|---|---|
| `omega-data-engineer-2026` | Data Engineer | Aucune restriction |
| `omega-data-analyst-2026` | Data Analyst | Aucune restriction |
| `omega-norddrive-2026` | Référent client | NordDrive uniquement |
| `omega-freshmarket-2026` | Référent client | FreshMarket uniquement |
| `omega-mediotex-2026` | Référent client | MedioTex uniquement |

### 2.2 Autorisation par groupe

Modèle d'accès repris de
[`registre_rgpd.md` §4](registre_rgpd.md#4-droits-daccès) :

| Endpoint | Data Engineer / Analyst | Référent client |
|---|---|---|
| `GET /commandes-clients` | Tous clients | **Restreint à son client** (le paramètre `client` demandé est ignoré, pas seulement validé) |
| `GET /commandes-clients/{id}/lignes` | Toute commande | Uniquement les commandes de son client (403 sinon) |
| `GET /livraisons` | Autorisé | **403** — données de transport hors périmètre client (voir ci-dessous) |
| `GET /kpis/taux-service` | Tous clients | Restreint à son client |

`/livraisons` est réservé aux rôles internes : la table `livraisons`
porte les seules colonnes réellement personnelles du programme
(`tournees.chauffeur`, `livraisons.adresse_livraison` — voir
[`registre_rgpd.md` §1](registre_rgpd.md#1-données-personnelles-réellement-présentes)),
et n'a de toute façon aucun lien exploitable avec un client (voir
[`modelisation_merise.md` §4.2](modelisation_merise.md#42-commandes_clients-reste-indépendante-de-commandes-fluxpro)) :
plutôt que de construire un filtrage partiel et fragile, l'accès est
refusé en bloc aux référents externes — cohérent avec le principe de
minimisation déjà retenu.

---

## 3. Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Disponibilité du service (sans authentification) |
| GET | `/commandes-clients` | En-têtes de commandes clients consolidées (C10/C11), filtrables par client, paginées |
| GET | `/commandes-clients/{id}/lignes` | Lignes d'une commande (produit, quantité, poids, chaîne du froid — dérivés de `produits` FluxPro via `sku`) |
| GET | `/livraisons` | Livraisons TransFlow avec statut dérivé (équipes internes uniquement) |
| GET | `/kpis/taux-service` | Taux de service (% livré à l'heure) par client, calculé sur FluxPro |

Documentation interactive complète (OpenAPI) : `/docs` une fois le
service lancé.

---

## 4. Lancement

### En local

```bash
pip install -r requirements-dev.txt
uvicorn datacore.api.main:app --reload
# -> http://127.0.0.1:8000/docs
```

### Via Docker Compose

```bash
cp .env.example .env
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d --build
# -> http://localhost:8000/docs (port configurable via OMEGA_DATA_API_PORT)
```

Le service `omega-data-api` attend que `db` soit `healthy`
(`depends_on: condition: service_healthy`) et surcharge `STAGING_DB_DSN`
pour joindre la base via le nom de service Docker (`db`) plutôt que
`localhost`.

---

## 5. Exemples réels

Vérifiés de bout en bout (Docker Compose + C8 + C10 + C11 peuplés) :

```bash
# Rejeté sans clé API
curl http://localhost:8000/commandes-clients
# -> 401

# Data Engineer : consulte n'importe quel client
curl -H "X-API-Key: omega-data-engineer-2026" \
  "http://localhost:8000/commandes-clients?client=NordDrive&limit=2"

# Référent NordDrive demandant FreshMarket -> ramené à son périmètre
curl -H "X-API-Key: omega-norddrive-2026" \
  "http://localhost:8000/commandes-clients?client=FreshMarket"
# -> renvoie les commandes NordDrive, pas FreshMarket

# Référent client sur /livraisons -> 403
curl -H "X-API-Key: omega-norddrive-2026" http://localhost:8000/livraisons
# -> 403

# KPI taux de service, tous clients (Data Analyst)
curl -H "X-API-Key: omega-data-analyst-2026" http://localhost:8000/kpis/taux-service
# -> [{"client":"FreshMarket","nb_expeditions":245,"taux_service_pct":90.6}, ...]
```

---

## 6. Tests

- `tests/unit/test_api_repository.py` : requêtes SQL de la couche
  d'accès (filtres, jointures), avec des doubles de connexion.
- `tests/integration/test_api_routes.py` : authentification,
  autorisation par rôle, codes HTTP, via le `TestClient` FastAPI (couche
  d'accès aux données mockée — ne re-teste pas le SQL).
- Test de bout en bout manuel (Docker Compose) documenté au §5 :
  authentification, restriction de périmètre client, refus d'accès aux
  livraisons pour un référent, KPI correctement filtré.
