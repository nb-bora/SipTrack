# SipTrack — Documentation de référence

> Le registre incontestable du bar. Documentation vivante du **domaine métier** et de
> l'**architecture** de SipTrack.

## À quoi sert ce dossier

SipTrack est un outil de **gestion et d'audit** pour bars au Cameroun. Cette documentation
fige le fruit de la phase de *Product Discovery* : le métier, le langage commun, les règles,
et l'architecture technique. Elle est le **contrat partagé** par les trois briques du projet
(`Backend/`, `Frontend/`, `Mobile/`).

Elle doit rester **vivante** : toute décision structurante nouvelle passe par un ADR
(voir [`decisions/`](./decisions/)) ; tout changement de règle métier mène à une mise à jour
de [`02-modele-metier.md`](./02-modele-metier.md).

## Ordre de lecture recommandé

1. [`01-glossaire-ubiquitaire.md`](./01-glossaire-ubiquitaire.md) — le **langage commun**.
   À lire en premier : chaque mot y a un sens unique et non négociable.
2. [`02-modele-metier.md`](./02-modele-metier.md) — le **modèle métier** : acteurs,
   objets, événements, cycles de vie, invariants, architecture de contrôle.
3. [`03-architecture-backend.md`](./03-architecture-backend.md) — le **blueprint technique**
   (DDD + Clean Architecture sur Django).
4. [`decisions/`](./decisions/) — les **décisions d'architecture** (ADR), et leur *pourquoi*.

## Statut

| Élément | Statut |
|---|---|
| Modèle métier (cœur) | ✅ Validé en découverte |
| Blueprint d'architecture | ✅ Validé (conceptuel) |
| Périmètre V1 | Bar d'ambiance · boissons uniquement · outil interne (2-3 bars) |
| Prochaine étape | Tranche verticale (« walking skeleton ») — 1 cas d'usage de bout en bout |

## Principes fondateurs (à ne jamais perdre de vue)

1. **La confiance ne se décrète pas, elle se prouve.** On ne surveille personne ; on rend
   les faits incontestables — et **personne n'échappe au journal, pas même le propriétaire**.
2. **Le journal des Mouvements est la seule vérité.** Tous les états (stock, caisse,
   créances) sont des **conséquences calculées**, jamais des données saisies.
3. **La caissière honnête est protégée** autant que le propriétaire est renseigné :
   c'est la condition de l'adoption sur le terrain.
