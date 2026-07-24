# ADR-0005 — Isolation stricte des bounded contexts (pas de FK ORM)

- **Statut** : ✅ Accepté — 2026-07-24
- **Contexte** : Les contextes (Service & Ventes, Stock, Crédit, Approvisionnement, Catalogue,
  Gouvernance) partagent la même base Django. L'ORM **tente** de créer des `ForeignKey` entre
  apps, ce qui **couplerait** les contextes et casserait leurs frontières.

## Options envisagées

1. **FK ORM libres entre apps** — pratique Django habituelle, mais soude les contextes,
   empêche leur évolution indépendante, brouille la propriété des données.
2. **Isolation stricte** : aucune FK inter-contexte ; référence par **identifiant** ;
   intégration par **Domain Events**, **Anti-Corruption Layer** et **Published Language**.

## Décision

Option 2.

- **Aucune `ForeignKey` ORM entre bounded contexts.** Les FK ne sont autorisées qu'à
  l'**intérieur** d'un contexte.
- Intégration inter-contexte via : **ID** (référence faible), **Domain Events** (réaction
  eventual), **ACL** (traduction du monde externe / d'un autre contexte), **Published
  Language** (contrat de la Gouvernance : rôles, capacité, délégation).
- Donnée nécessaire à un instant précis → **copiée dans un VO** (ex. `PrixDate` gravé sur la
  vente), jamais lue en direct par FK.

## Conséquences

- ➕ Contextes réellement autonomes ; évolution et test indépendants.
- ➕ L'historique reste vrai (le prix gravé ne change pas si le catalogue change).
- ➖ Pas d'intégrité référentielle DB inter-contexte : elle est portée par le **domaine et les
   use cases**, pas par la base. À assumer et tester.
- ➖ Un peu de duplication assumée (copies de VO) au profit de l'autonomie.
