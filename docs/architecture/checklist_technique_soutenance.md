# Checklist technique pré-soutenance — issue #99

**But** : vérifier les 4 points techniques propres à Slidev (outil retenu,
voir issue #97) avant d'entrer en salle. Pour l'infrastructure (services
Docker, Airflow, identifiants), voir
[`script_demo_soutenance.md` §Préparation](script_demo_soutenance.md) —
pas dupliqué ici.

À relancer le jour J (`npm run dev` dans `slides/`, serveur sur
`localhost:3030`) : les captures/commandes ci-dessous datent du 19/11/2026,
avant la dernière relecture — un futur changement de `slides.md` peut
changer le résultat.

## 1. Panneau « Goto » masqué

Le panneau de navigation Slidev (plein écran, précédent/suivant, bouton
« Show slide overview » — le vrai nom du panneau « Goto ») est caché par
défaut (`opacity-0`, visible seulement au survol direct du coin
bas-gauche) — risque résiduel : un mouvement de souris accidentel pendant
la présentation l'affiche devant le jury. [`slides/style.css`](../../slides/style.css)
le masque explicitement (`display: none !important`), sans affecter le
mode présentateur (fenêtre séparée, contrôles propres).

Vérification :
```js
// Playwright, depuis slides/ (npm run dev doit tourner sur :3030)
const el = await page.$('.slidev-slide-container > .absolute.bottom-0.left-0');
await el.evaluate(e => getComputedStyle(e).display); // doit retourner "none"
```
**Statut (19/11/2026) : OK.** Vérifié en vue normale (`display: none`
confirmé) et en mode présentateur (`/presenter/1`, contrôles présentateur
intacts, capture d'écran prise).

## 2. Notes présentateur présentes sur chaque slide

Visibles uniquement en mode présentateur (`/presenter`), jamais dans
l'export public/PDF.

Vérification (boucle sur les 55 slides via `/presenter/<n>`, lit le
panneau de notes) :
```js
for (let i = 1; i <= 55; i++) {
  await page.goto(`http://localhost:3030/presenter/${i}`);
  const text = await page.evaluate(() =>
    document.querySelector('.overflow-auto.prose, .slidev-note, .prose')?.textContent.trim());
  if (!text) console.log('slide sans notes :', i);
}
```
**Statut (19/11/2026) : OK.** 55/55 slides ont des notes réelles et
distinctes (vérifié par échantillonnage du contenu, pas seulement
présence/absence — slides 1, 15, 30, 47, 55 relues).

## 3. Mode présentateur accessible

`localhost:3030/presenter/1` (ou le bouton dédié depuis la vue normale) —
panneau de gauche la slide courante, panneau de droite la suivante +
notes + minuteur.

**Statut (19/11/2026) : OK.** Chargé et capturé sans erreur.

## 4. Toutes les images se chargent correctement

Aucune image cassée (chemin erroné, fichier manquant dans
`slides/public/`) sur les 55 slides.

Vérification (boucle sur les 55 slides, filtre les `<img>` dont
`naturalWidth === 0`, signe d'un échec de chargement) :
```js
for (let i = 1; i <= 55; i++) {
  await page.goto(`http://localhost:3030/${i}`);
  const bad = await page.evaluate(() =>
    Array.from(document.querySelectorAll('img'))
      .filter(img => img.naturalWidth === 0)
      .map(img => img.getAttribute('src')));
  if (bad.length) console.log(i, bad);
}
```
**Statut (19/11/2026) : OK.** 0 image cassée sur les 55 slides.

## À refaire si `slides.md` change après ce point

Les 4 vérifications ci-dessus sont rapides (quelques secondes chacune,
serveur `npm run dev` déjà lancé) — les relancer après toute modification
ultérieure de `slides.md`, pas seulement se fier à ce document.
