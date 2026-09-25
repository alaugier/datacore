"""Test d'intégration de la restitution OMEGA BI dans Grafana (C16bis).

Vérifie contre une vraie instance Grafana (Docker Compose) que le
provisioning automatique (source de données + dashboard) fonctionne
réellement, et que le rôle `bi_reader` reste correctement restreint côté
Grafana -- pas seulement côté Postgres (déjà couvert par les GRANT SQL).

**Ignoré (skip), pas échoué, si l'infrastructure n'est pas démarrée** :

    docker compose -f infra/docker/docker-compose.yml --env-file .env up -d db grafana
    pytest tests/integration/test_grafana_omega_bi.py -v
"""
import socket

import pytest
import requests

from datacore.config import GRAFANA_ADMIN_PASSWORD, GRAFANA_ADMIN_USER, GRAFANA_PORT

GRAFANA_URL = f"http://localhost:{GRAFANA_PORT}"
AUTH = (GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD)


def _infra_disponible(hote: str, port: int, delai: float = 1.0) -> bool:
    """Teste une connexion TCP simple, sans dépendance à un client applicatif."""
    try:
        with socket.create_connection((hote, port), timeout=delai):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _infra_disponible("localhost", int(GRAFANA_PORT)),
    reason=(
        "Grafana non accessible -- lancer "
        "`docker compose -f infra/docker/docker-compose.yml --env-file .env up -d db grafana` "
        "avant ce test"
    ),
)


def test_grafana_est_en_sante():
    """L'API `/api/health` répond et la base interne de Grafana est accessible."""
    reponse = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
    assert reponse.status_code == 200
    assert reponse.json()["database"] == "ok"


def test_source_de_donnees_omega_bi_provisionnee_et_connectee():
    """La source Postgres provisionnée automatiquement se connecte réellement,
    avec les identifiants bi_reader (pas un compte admin Postgres)."""
    reponse = requests.get(
        f"{GRAFANA_URL}/api/datasources/uid/omega_bi_reader/health", auth=AUTH, timeout=5
    )
    assert reponse.status_code == 200
    assert reponse.json()["status"] == "OK"


def test_source_de_donnees_declare_une_base_par_defaut_dans_jsondata():
    """`jsonData.database` doit être renseigné, pas seulement le champ
    `database` de premier niveau -- sinon l'éditeur de requête du
    navigateur refuse d'exécuter la moindre requête ("You do not
    currently have a default database configured for this data
    source."), alors que `/health` et `/api/ds/query` fonctionnent très
    bien sans lui : cette vérification côté client (React) n'est pas
    exercée par un appel HTTP direct à l'API, contrairement aux deux
    tests précédents -- régression réelle trouvée le 25/09/2026 en
    testant depuis un vrai navigateur, invisible depuis les tests ci-dessus."""
    reponse = requests.get(
        f"{GRAFANA_URL}/api/datasources/uid/omega_bi_reader", auth=AUTH, timeout=5
    )
    assert reponse.status_code == 200
    assert reponse.json()["jsonData"].get("database")


def test_panel_taux_de_service_affiche_une_barre_par_client_pas_une_seule_valeur_reduite():
    """`reduceOptions.values` doit être `true` sur le panel bargauge --
    sans lui, Grafana réduit les 3 lignes (une par client) à une seule
    valeur agrégée ("Last *", ici la dernière du tri) au lieu d'une
    barre par client, silencieusement (aucune erreur, juste un panel
    qui affiche moins de données que prévu). Régression réelle trouvée
    le 25/09/2026, remontée par l'utilisateur après le correctif
    précédent ("No data" résolu, mais un seul client visible sur 3)."""
    reponse = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/sla-omega-bi", auth=AUTH, timeout=5)
    assert reponse.status_code == 200
    panel_bargauge = next(
        p for p in reponse.json()["dashboard"]["panels"] if p["type"] == "bargauge"
    )
    assert panel_bargauge["options"]["reduceOptions"]["values"] is True


def test_dashboard_sla_provisionne_avec_les_3_panels():
    """Le dashboard SLA est provisionné automatiquement (pas créé à la main)
    et reprend bien les 3 indicateurs (gestion_operationnelle_omega_bi.md §3.1-3.3)."""
    reponse = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/sla-omega-bi", auth=AUTH, timeout=5)
    assert reponse.status_code == 200
    panels = reponse.json()["dashboard"]["panels"]
    assert len(panels) == 3
    titres = {p["title"] for p in panels}
    assert any("taux de service" in t.lower() for t in titres)
    assert any("délai moyen" in t.lower() for t in titres)
    assert any("stock disponible" in t.lower() for t in titres)


def _interroger(sql: str) -> list:
    reponse = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        auth=AUTH,
        json={
            "queries": [
                {
                    "refId": "A",
                    "datasource": {"type": "postgres", "uid": "omega_bi_reader"},
                    "rawSql": sql,
                    "format": "table",
                }
            ]
        },
        timeout=5,
    )
    reponse.raise_for_status()
    return reponse.json()["results"]["A"]["frames"][0]["data"]["values"]


def test_les_3_panels_renvoient_des_donnees_reelles_de_lentrepot():
    """Chaque requête SQL des 3 panels s'exécute réellement contre l'entrepôt
    (pas seulement une vérification de syntaxe) et renvoie au moins une ligne."""
    taux_service = _interroger(
        "SELECT client, taux_service_pct FROM exploitation.v_taux_service_client"
    )
    delai = _interroger(
        "SELECT transporteur, delai_moyen_jours FROM exploitation.v_delai_moyen_transporteur"
    )
    stock = _interroger(
        "SELECT entrepot, quantite_totale FROM exploitation.v_stock_disponible_site"
    )
    assert len(taux_service[0]) > 0
    assert len(delai[0]) > 0
    assert len(stock[0]) > 0


def test_bi_reader_reste_restreint_au_perimetre_deja_scope_c14():
    """Le rôle bi_reader utilisé par Grafana ne peut pas lire `gouvernance`
    (exclu par choix, voir gestion_operationnelle_omega_bi.md §4) -- vérifie
    que la restriction déjà actée côté Postgres est bien celle que Grafana
    utilise, pas un compte plus large configuré par erreur."""
    with pytest.raises(requests.HTTPError):
        _interroger("SELECT * FROM gouvernance.v_dernieres_operations LIMIT 1")
