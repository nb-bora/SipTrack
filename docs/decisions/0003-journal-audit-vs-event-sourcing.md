# ADR-0003 — Journal d'audit = exigence métier ; Event Sourcing = détail d'infra

- **Statut** : ✅ Accepté — 2026-07-24
- **Contexte** : Le métier exige un **journal inaltérable** (le `Mouvement` : append-only,
  contre-passation, reconstructibilité à toute date). On a d'abord confondu cette exigence avec
  l'**Event Sourcing** (technique de persistance). Ce sont deux choses distinctes.

## Options envisagées

1. **Full Event Sourcing** (état des agrégats dérivé d'un flux d'événements + projections) —
   puissant, alignement fort avec le journal, mais complexité élevée (versioning, snapshots,
   rejeu) pour un outil interne de 2-3 bars.
2. **State-based + journal d'audit append-only séparé** — les agrégats sont persistés par état ;
   un journal des Domain Events (le `Mouvement`) est écrit en append-only comme source d'audit.
   Plus simple, couvre l'exigence métier.
3. **Pas de journal dédié** (audit via logs applicatifs) — insuffisant : pas d'attribution ni
   de reconstructibilité fiables. Rejeté.

## Décision

- Le **journal d'audit est un concept du domaine** (exigence, pas technique).
- La **stratégie de persistance est un détail d'infra**, caché derrière un port `Journal`.
- On **démarre state-based** (option 2). Le passage à l'Event Sourcing reste possible plus tard
  **sans toucher au domaine** (on ne change qu'une implémentation d'infra).

## Conséquences

- ➕ Simplicité immédiate ; l'exigence d'audit (immutabilité, contre-passation,
   reconstructibilité) est satisfaite.
- ➕ CQRS (read models) reste possible indépendamment de ce choix.
- ➖ La reconstruction complète « à toute date » repose sur le journal + éventuels recomptages ;
   si un jour on veut la garantie totale par rejeu, migrer vers l'ES (chemin ouvert).
- Le journal impose `UPDATE`/`DELETE` interdits sur la table `Mouvement` (permissions DB).
