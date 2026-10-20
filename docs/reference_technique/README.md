# Référence technique — aide-mémoire par langage/outil

Pas de la documentation d'API générale (celle-ci existe déjà, très bien
faite, sur le site de chaque outil) : un aide-mémoire **ancré dans ce
que ce projet utilise réellement**, avec les arguments effectivement
passés et une ligne sur le piège qui aurait pu surprendre. L'objectif
n'est pas l'exhaustivité mais de ne pas re-découvrir deux fois la même
chose (« comment on avait fait, déjà ? »).

## Organisation

Un fichier par langage/outil, pas par librairie — une librairie qui
grossit peut être scindée dans son propre fichier plus tard (ex.
`python_boto3.md`), mais pas avant que ce soit nécessaire :

| Fichier | Couverture |
|---|---|
| [`python.md`](python.md) | Bibliothèques Python utilisées dans le code applicatif (`src/datacore/`) |
| `sql.md` | *(à créer)* Patterns SQL/PostgreSQL spécifiques au projet |
| [`shell.md`](shell.md) | Docker Compose (`.env`), provisioning Grafana (C16bis) |

## Comment ça s'enrichit

Au fil de l'eau, pas en une seule passe rétroactive sur tout le projet
(trop volumineux, et une bonne partie serait de la doc générique
copiée plutôt qu'un vrai retour d'expérience). Concrètement : dès
qu'un nouvel outil/une nouvelle bibliothèque est introduit(e) dans le
projet, ou qu'un usage non évident d'un outil déjà là s'avère utile à
retenir, une entrée est ajoutée ici — au même rythme que
`fiche_synthese.html` ou `veille_technique_reglementaire.md`, par
jalon plutôt que tout d'un coup.

## Format d'une entrée

```markdown
### `signature.de.la(fonction_ou_méthode)`
Une ligne : ce que ça fait, et le piège éventuel (import top-level vs
méthode d'instance, ordre des arguments, effet de bord non évident).
Utilisé dans : `chemin/du/fichier.py::nom_de_la_fonction()`
\`\`\`python
# l'appel réel du projet, pas un exemple générique
\`\`\`
```
