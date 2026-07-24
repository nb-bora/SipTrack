# ADR-0001 — Architecture en couches (Clean Architecture / DDD)

- **Statut** : ✅ Accepté — 2026-07-24
- **Contexte** : SipTrack est un système d'**audit** dont le cœur est une logique métier riche
  (services, réconciliations, délégation, invariants de conservation). Il doit rester testable,
  durable, et indépendant des choix techniques (base, framework, canaux d'accès).

## Options envisagées

1. **Django « classique » (fat models / MVT)** — rapide au début, mais la logique se disperse
   dans models/views/signals et devient soudée à l'ORM. Testabilité et évolutivité faibles.
2. **Clean Architecture en 4 couches (Domaine / Application / Infrastructure / Interface)** —
   plus de cérémonie initiale, mais isole la logique métier et rend le reste remplaçable.
3. **Microservices d'emblée** — sur-dimensionné pour un outil interne de 2-3 bars.

## Décision

On adopte **Clean Architecture en 4 couches**, avec la **règle de dépendance vers l'intérieur**
et DDD tactique (agrégats, VO, domain events, repositories). Le domaine est le centre ;
l'infrastructure implémente ses ports.

## Conséquences

- ➕ Logique métier isolée, testable sans base ni framework.
- ➕ Base, canaux (REST, sync mobile) et persistance interchangeables.
- ➖ Plus de code de « plomberie » (DTO, mappers, ports) — accepté et cadré par la discipline
  (import-linter, tests en pyramide).
- On **reste pragmatique** : 6 contextes, pas de micro-services.
