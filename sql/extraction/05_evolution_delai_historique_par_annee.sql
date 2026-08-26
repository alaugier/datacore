-- Objectif (C9) : évolution annuelle du délai moyen de livraison par
-- client sur l'historique — illustre une analyse de tendance sur la
-- source « système big data », hors périmètre opérationnel FluxPro
-- (qui ne couvre que les commandes en cours).
SELECT
    client,
    extract(YEAR FROM date_expedition) AS annee,
    count(*) AS nb_expeditions,
    round(avg(delai_livraison_jours), 1) AS delai_moyen_jours
FROM historique_expeditions
GROUP BY client, extract(YEAR FROM date_expedition)
ORDER BY client, annee;
