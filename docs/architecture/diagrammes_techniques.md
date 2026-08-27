# Diagrammes techniques — Ingestion (C8) et Omega Data API (C12)

Diagrammes Mermaid illustrant l'architecture réelle des deux modules les
plus structurants du Bloc 2 : la collecte multi-source (C8) et l'API
d'exposition (C12). Objectif double : documentation immédiate (rendue
nativement par GitHub) et matière prête à intégrer au futur rapport
technique LaTeX (M4, transverse) — voir §4 pour l'export en image.

---

## 1. Architecture de l'ingestion (C8)

Les cinq connecteurs (`src/datacore/ingestion/`) sont indépendants les
uns des autres et convergent tous vers la même zone d'atterrissage
intermédiaire (`data/interim/`, voir
[`sequencement_bloc2.md`](sequencement_bloc2.md)), avant que C10
(nettoyage) et C11 (chargement en base) ne les consomment.

```mermaid
flowchart LR
    subgraph Sources["Sources de données (voir topographie, C2)"]
        direction TB
        A1["API TransFlow<br/>(service web)"]
        A2["Portail transporteur<br/>(scraping)"]
        A3["Base FluxPro<br/>(PostgreSQL, schema.sql fourni)"]
        A4["Fichiers clients bruts<br/>(3 formats hétérogènes)"]
        A5["Historique<br/>(CSV, 25 000 lignes)"]
    end

    subgraph Connecteurs["src/datacore/ingestion/ (C8)"]
        direction TB
        B1["transflow.py"]
        B2["portail_scraping.py"]
        B3["fluxpro.py"]
        B4["clients_files.py"]
        B5["historique.py"]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    A5 --> B5

    L[("data/interim/<br/>zone d'atterrissage (JSON, non versionnée)")]

    B1 --> L
    B2 --> L
    B3 --> L
    B4 --> L
    B5 --> L

    L --> C10["processing/clients_cleaning.py<br/>(C10 — nettoyage)"]
    L --> C11["storage/staging/load_staging.py<br/>(C11 — chargement)"]
    C11 --> DB[("Base de travail<br/>PostgreSQL")]
```

**Points clés reflétés dans le diagramme** : chaque connecteur ne fait
qu'extraire et écrire dans la zone d'atterrissage (aucune logique de
nettoyage ni de modélisation à ce stade — voir la justification du
séquencement C8 → C10 → C9 → C11 → C12) ; `fluxpro.py` lit directement
la base déjà peuplée (issue #7), les quatre autres connecteurs
interrogent des sources externes (API, HTML, fichiers).

---

## 2. Architecture de l'Omega Data API (C12)

### 2.1 Organisation des modules

```mermaid
flowchart TB
    Client["Client HTTP<br/>(équipes BI, data science, notebook de démo)"]
    Client -->|"GET + en-tête X-API-Key"| Main["main.py<br/>(routes FastAPI)"]
    Main --> Auth["auth.py<br/>(authentification + autorisation)"]
    Auth --> Config["config.py<br/>(clés API -> Principal)"]
    Main --> Db["db.py<br/>(connexion par requête)"]
    Main --> Repo["repository.py<br/>(accès SQL)"]
    Main --> Schemas["schemas.py<br/>(modèles Pydantic -> spec OpenAPI)"]
    Repo --> Db
    Db --> Postgres[("Base de staging<br/>PostgreSQL")]
```

### 2.2 Séquence d'autorisation — le comportement critique

Le comportement le plus important de l'API n'est pas visible dans le
diagramme de modules ci-dessus : un référent client n'est pas seulement
*rejeté* s'il demande les données d'un autre client, il est
*silencieusement ramené* à son propre périmètre. Ce diagramme de
séquence illustre ce cas réel (vérifié en conditions réelles, voir
[`api_omega_data.md` §5](api_omega_data.md#5-exemples-réels) et
[`notebooks/demo_omega_data_api.ipynb`](../../notebooks/demo_omega_data_api.ipynb)).

```mermaid
sequenceDiagram
    actor C as Référent NordDrive
    participant M as main.py (route)
    participant A as auth.py
    participant R as repository.py
    participant DB as Base de staging

    C->>M: GET /commandes-clients?client=FreshMarket<br/>X-API-Key: omega-norddrive-2026
    M->>A: get_current_principal(api_key)
    A-->>M: Principal(role=CLIENT_REFERENT, client="NordDrive")
    M->>M: _resolve_client_scope(principal, "FreshMarket")<br/>-> "NordDrive" (paramètre demandé ignoré)
    M->>R: list_commandes_clients(db, client="NordDrive")
    R->>DB: SELECT ... WHERE client = 'NordDrive'
    DB-->>R: lignes NordDrive uniquement
    R-->>M: résultats
    M-->>C: 200 OK — commandes NordDrive (jamais FreshMarket)
```

---

## 3. Sources de ces diagrammes

Ces diagrammes décrivent le code réellement livré (pas une intention) :
`src/datacore/ingestion/` (C8, PR #33), `src/datacore/api/` (C12, PR #41).
Toute évolution de ces modules doit s'accompagner d'une mise à jour de
ce document.

## 4. Export pour le rapport LaTeX (M4, transverse)

Mermaid n'est pas nativement supporté par LaTeX. Au moment de rédiger le
rapport technique (milestone M4, prévu plus tard), ces diagrammes
devront être exportés en image (SVG/PDF) — par exemple via
[`mermaid-cli`](https://github.com/mermaid-js/mermaid-cli)
(`mmdc -i diagrammes_techniques.md -o diagramme.svg`) — puis inclus avec
`\includegraphics`. Non fait à ce stade : action reportée à M4, cette
page reste la source de vérité éditable en attendant.
