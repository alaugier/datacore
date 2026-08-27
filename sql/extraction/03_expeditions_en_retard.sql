-- Objectif (C9) : expéditions livrées en retard (date réelle postérieure
-- à la date prévue), avec le nombre de jours de retard — alimente
-- directement l'indicateur « taux de service » attendu par la Direction
-- des Opérations (voir docs/architecture/etude_faisabilite.md §4).
SELECT
    exp.tracking_number,
    exp.transporteur,
    c.nom AS client,
    exp.date_livraison_prevue,
    exp.date_livraison_reelle,
    (exp.date_livraison_reelle - exp.date_livraison_prevue) AS jours_retard
FROM expeditions exp
JOIN commandes cmd ON cmd.id = exp.commande_id
JOIN clients c ON c.id = cmd.client_id
WHERE exp.date_livraison_reelle IS NOT NULL
  AND exp.date_livraison_reelle > exp.date_livraison_prevue
ORDER BY jours_retard DESC;
