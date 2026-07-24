# ADR-0004 — Petits agrégats, référence par identité, cohérence eventual

- **Statut** : ✅ Accepté — 2026-07-24
- **Contexte** : Le domaine comporte des concepts liés (Service, Addition, Sous-caisse, Crédit,
  Livraison, Inventaire). Il faut décider des **frontières transactionnelles** (agrégats) et
  éviter les gros agrégats sous contention.

## Options envisagées

1. **Gros agrégat `Service`** contenant additions, sous-caisses, mouvements — invariants
   immédiats faciles, mais agrégat énorme (toute une soirée), contention, chargement lourd.
2. **Petits agrégats séparés** référencés par identité, cohérence inter-agrégats **eventual**
   (via Domain Events) — conforme aux règles de Vernon (*Effective Aggregate Design*).

## Décision

Option 2, en appliquant les **4 règles de Vernon** :
1. Ne modéliser dans un agrégat que ses **vrais invariants immédiats**.
2. **Petits agrégats** : `Service`, `Addition`, `SousCaisseServeuse`, `Credit`, `Livraison`,
   `Inventaire` sont **séparés**.
3. **Référence par identité** (ID), jamais par objet.
4. **Cohérence eventual** hors frontière, via Domain Events.

Exemple : « on ne clôture pas un service tant qu'une addition est ouverte » n'est **pas** un
invariant d'un seul agrégat → **use case applicatif** qui vérifie les additions ouvertes avant
d'émettre `ServiceCloture`.

## Conséquences

- ➕ Agrégats petits, performants, faciles à raisonner et tester.
- ➕ `Une transaction = un agrégat`.
- ➖ Certaines règles deviennent **coordonnées** (use case / events) et non transactionnelles :
   il faut assumer une cohérence *eventual* et concevoir les use cases en conséquence.
