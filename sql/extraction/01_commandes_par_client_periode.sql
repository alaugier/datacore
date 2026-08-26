-- Objectif (C9) : nombre de commandes et quantité totale par client et
-- par mois, sur la base FluxPro (commandes + lignes_commande).
-- Sert de brique pour le futur tableau de bord OMEGA BI (bloc 3, C13 —
-- taux de service par client/période).
SELECT
    c.nom AS client,
    date_trunc('month', cmd.date_commande) AS mois,
    count(DISTINCT cmd.id) AS nb_commandes,
    sum(lc.quantite) AS quantite_totale
FROM commandes cmd
JOIN clients c ON c.id = cmd.client_id
JOIN lignes_commande lc ON lc.commande_id = cmd.id
GROUP BY c.nom, date_trunc('month', cmd.date_commande)
ORDER BY client, mois;
