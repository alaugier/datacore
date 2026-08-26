-- Objectif (C9) : stocks actuels par entrepôt et produit, avec repère
-- de rupture (quantité = 0) — répond à l'irritant remonté par les
-- responsables d'entrepôt en entretien (voir docs/architecture/
-- etude_faisabilite.md §2.3) : « les ruptures de stock ne sont
-- détectées que lorsqu'une commande échoue ».
SELECT
    e.nom AS entrepot,
    p.sku,
    p.libelle,
    s.quantite,
    s.date_maj,
    (s.quantite = 0) AS en_rupture
FROM stocks s
JOIN entrepots e ON e.id = s.entrepot_id
JOIN produits p ON p.id = s.produit_id
ORDER BY en_rupture DESC, entrepot, sku;
