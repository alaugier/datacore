# Séquencement du milestone M5 — Rapport LaTeX

Même principe que [`sequencement_bloc2.md`](sequencement_bloc2.md)/
[`sequencement_bloc3.md`](sequencement_bloc3.md)/
[`sequencement_bloc4.md`](sequencement_bloc4.md) : décider l'ordre et le
découpage avant de rédiger, pas en cours de route. M5 n'est pas un bloc
de compétences RNCP (contrairement aux Blocs 1-4) — c'est le jalon
transverse de rédaction du rapport. Structure proposée par la
référente technique (Sophie MARTIN, revue technique et arbitrages
d'architecture — voir [`feuille_de_route.md` §2](feuille_de_route.md#2-composition-de-léquipe-projet))
et validée le 20/10/2026.

---

## 1. Structure du document

- `docs/latex/rapport.tex` (document maître) + `chapitres/00` à `07` +
  `figures/` + `annexes/` (matrice compétences, glossaire).
- **Rapport synthétique + renvois au dépôt GitHub pour le détail
  technique exhaustif** — pas de reproduction complète du contenu de
  `docs/architecture/` dans le corps du texte. Chaque chapitre cite ses
  sources (`sequencement_blocN.md`, comptes rendus `MN.md`, livrables
  technique) plutôt que de les recopier.
- Extraits de code ciblés, 1-2 par chapitre maximum, uniquement pour
  illustrer une décision déjà justifiée dans le texte (jamais pour
  montrer de la syntaxe seule). Candidats déjà identifiés : vérification
  `tracking_number` (C11), mécanisme SCD2 (C17), configuration
  `httpfs`/MinIO (C19), `verifier_cle_configuree()` (C21) — à confirmer
  ou substituer au moment de rédiger chaque chapitre, selon ce qui sert
  réellement le propos.

## 2. Plan des chapitres

| # | Chapitre | S'appuie sur |
|---|---|---|
| 00 | Introduction (contexte, problématique, objectifs, plan) | `etude_faisabilite.md` §1 |
| 01 | Bloc 1 — Cadrage (C1-C7) | 7 livrables mergés (M0) |
| 02 | Bloc 2 — Collecte & Stockage (C8-C12) | `sequencement_bloc2.md` + 5 livrables (M1) |
| 03 | Bloc 3 — Entrepôt OMEGA BI (C13-C17) | `sequencement_bloc3.md` + 5 livrables (M2) |
| 04 | Bloc 4 — Data Lake OMEGA LAKE (C18-C21) | `sequencement_bloc4.md` + 4 livrables (M3) |
| 05 | Restitution BI (Grafana, jalon M4) | `gestion_operationnelle_omega_bi.md` §3.5, `monitoring_lake.md`, `comptes_rendus/M4.md` |
| 06 | Synthèse transverse | **À rédiger, pas une recopie** — budget cumulé (4 blocs + M4), bilan qualité (évolution du nombre de tests M0→M4), bilan RGPD/RGESN/RGAA comme fil narratif (le parcours pseudonymisation complet, du premier risque identifié en C18 au correctif de clé en M3) |
| 07 | Conclusion | Objectifs SMART (`etude_faisabilite.md` §7), limites connues (agrégation des "points ouverts" des 5 `MN.md`), apprentissages |
| — | Annexe : matrice chapitre ↔ compétence(s) Cx ↔ épreuve(s) Ex ↔ document source | Pour que le jury retrouve rapidement la preuve de chaque compétence |

## 3. Découpage en issues et ordre de rédaction

Décision du 20/10/2026, tranchée entre trois options (une issue par
chapitre, une seule issue monolithique, un découpage par niveau de
risque) — la troisième retenue :

| Issue | Portée | Niveau de risque |
|---|---|---|
| 1 | Chapitres 01-05 | Faible — synthèse de contenu déjà écrit, vérifié et mergé sur `dev` pour chaque bloc clos |
| 2 | Chapitre 06 (Synthèse transverse) | Élevé — vraie rédaction, pas de source à synthétiser directement ; traité seul pour lui donner le soin nécessaire, pas noyé dans le reste |
| 3 | Chapitres 00/07 + Annexe | Dépend des chapitres 01-06 stabilisés — l'introduction et la conclusion ne peuvent pas être écrites avant que le corps du rapport soit arrêté |

**Pourquoi pas une issue par chapitre** : 9 issues pour un livrable qui
reste fondamentalement un document unique — trop de frais de gestion
pour la granularité réelle du travail (chapitres 01-04 notamment sont
individuellement courts, de la synthèse directe des comptes rendus déjà
rédigés).

**Pourquoi pas une seule issue monolithique** : perdrait la visibilité
Kanban sur la progression, et romprait avec la granularité tenue sur le
reste du programme (y compris pour des correctifs mineurs, ex. PR #84).

**Ordre retenu : Issue 1 → Issue 2 → Issue 3.** Aucune alternative
sérieuse : la synthèse transverse (06) a besoin que les chapitres par
bloc (01-05) existent déjà pour pouvoir les consolider (budget cumulé,
évolution des tests, fil RGPD/RGESN) ; l'introduction et la conclusion
(00/07) ont besoin que tout le reste soit stable pour annoncer le plan
et en tirer un bilan qui ne sera pas contredit par une rédaction encore
en cours.
