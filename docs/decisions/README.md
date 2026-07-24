# Architecture Decision Records (ADR)

Ce dossier trace les **décisions d'architecture structurantes** de SipTrack, et surtout leur
*pourquoi*. Format : **MADR** (Markdown ADR) — variante de Nygard incluant les *options
envisagées*, recommandée quand le rationnel et les alternatives comptent.

## Règles

- Un ADR = **une** décision. Numérotation séquentielle.
- Un ADR accepté est **immuable** : on ne l'édite pas, on le **remplace** (statut `Superseded`).
- Sections : *Statut · Contexte · Options envisagées · Décision · Conséquences*.

## Index

| # | Décision | Statut |
|---|---|---|
| [0001](./0001-clean-architecture-en-couches.md) | Architecture en couches (Clean Architecture / DDD) | ✅ Accepté |
| [0002](./0002-domaine-independant-de-django.md) | Domaine indépendant de Django (persistence-ignorant) | ✅ Accepté |
| [0003](./0003-journal-audit-vs-event-sourcing.md) | Journal d'audit = exigence métier ; ES = détail d'infra | ✅ Accepté |
| [0004](./0004-petits-agregats-coherence-eventual.md) | Petits agrégats, référence par identité, cohérence eventual | ✅ Accepté |
| [0005](./0005-isolation-bounded-contexts.md) | Isolation stricte des bounded contexts (pas de FK ORM) | ✅ Accepté |
