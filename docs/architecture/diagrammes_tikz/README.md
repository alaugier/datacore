# MCD / MLD réels (LaTeX/TikZ) — annexe soutenance

Deux diagrammes stricts (cardinalités Merise (min,max) pour le MCD,
tables typées + flèches FK pour le MLD), en complément du diagramme
Mermaid hybride MCD/MLD utilisé partout ailleurs dans le programme (voir
`docs/architecture/modelisation_merise.md` §2 et l'annexe « MCD / MLD /
MPD » du diaporama de soutenance).

Périmètre volontairement réduit aux 7 entités modélisées/liées en C11
(`TRANSPORTEURS`, `TOURNEES`, `LIVRAISONS`, `EXPEDITIONS`,
`COMMANDES_CLIENTS`, `LIGNES_COMMANDE_CLIENTS`, `PRODUITS`) plutôt que
les 14 entités du modèle complet — lisibilité sur un diagramme unique ;
le modèle complet reste `modelisation_merise.md` §2.

Compilation (nécessite `pdflatex` + le paquet `standalone`) :

```bash
pdflatex modelisation_merise_mcd_reel.tex
pdftoppm -r 220 -png modelisation_merise_mcd_reel.pdf sortie
```

PNG exportés utilisés par le diaporama :
`slides/public/images/modelisation_merise_mcd_reel.png` et
`..._mld_reel.png`.
