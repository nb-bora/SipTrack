# 📖 Domaine : Gouvernance & Accès

Qui a le droit d'écrire dans le journal, et sous quelle identité.

**État : amorce.** Ce contexte n'expose aujourd'hui qu'une couche interface —
l'obtention d'un jeton. Il n'a ni domaine ni application, parce que
l'authentification n'est pas une règle métier mais un service technique.

## Fonctionnalités

### ✅ Livrées

| # | Fonctionnalité | Doc |
|---|---|---|
| 1 | Authentifier les requêtes et attribuer les faits | [Lire](./01-authentifier-les-requetes.md) |

### 📋 Prévues

| # | Fonctionnalité | Pourquoi |
|---|---|---|
| 2 | Acteurs et capacités | Remplacer l'utilisateur Django par un véritable agrégat `Acteur` |
| 3 | Délégation à trois niveaux | Réservé (gérante) · sous politique (crédit) · pleinement délégué |
| 4 | Validations | Ce que la gérante doit contresigner |

Voir [docs/02-modele-metier.md §3](../../02-modele-metier.md) pour le modèle cible.

## Ce que ce contexte ne fait pas encore

L'authentification prouve **qui** écrit. Elle ne dit rien de **ce que cette
personne a le droit de faire** : aujourd'hui tout compte authentifié peut tout
faire. Les régimes de décision (casser un prix, offrir, prélever) ne sont pas
implémentés — c'est la fonctionnalité #3.

C'est une limite assumée et connue, pas un oubli : elle est sans danger tant que
l'outil tourne en interne sur 2-3 bars avec des comptes créés à la main, et elle
devient bloquante dès qu'un compte est confié à quelqu'un dont on ne veut pas
qu'il puisse tout faire.

---

**Dernière mise à jour** : 2026-07-28
