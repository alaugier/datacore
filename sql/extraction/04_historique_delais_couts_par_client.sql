-- Objectif (C9) : délai moyen de livraison, coût de transport moyen et
-- taux de retard par client, sur l'historique volumineux (25 000
-- lignes, 2022-2026) chargé dans la base de staging (voir
-- scripts/load_historique.sh). Illustre l'extraction depuis la source
-- « système big data » attendue par le référentiel (C8/C9).
SELECT
    client,
    count(*) AS nb_expeditions,
    round(avg(delai_livraison_jours), 1) AS delai_moyen_jours,
    round(avg(cout_transport_eur), 2) AS cout_moyen_eur,
    round(
        100.0 * sum(CASE WHEN statut = 'Retardee' THEN 1 ELSE 0 END) / count(*),
        1
    ) AS taux_retard_pct
FROM historique_expeditions
GROUP BY client
ORDER BY taux_retard_pct DESC;
