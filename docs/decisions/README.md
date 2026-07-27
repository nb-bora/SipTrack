# 📖 Architecture Decision Records (ADR)

Ce dossier trace les **décisions d'architecture structurantes** de SipTrack, et surtout leur
*pourquoi*. Format : **MADR** (Markdown ADR) — variante de Nygard incluant les *options
envisagées*, recommandée quand le rationnel et les alternatives comptent.

## 🚀 Démarrer par la synthèse

👉 **[SYNTHESE-ADR.md](./SYNTHESE-ADR.md)** — Résumé exécutif de chaque ADR avec **exemples concrets du code livré**.
C'est le point de départ si vous découvrez l'architecture.

## Règles

- Un ADR = **une** décision. Numérotation séquentielle.
- Un ADR accepté est **immuable** : on ne l'édite pas, on le **remplace** (statut `Superseded`).
- Sections : *Statut · Contexte · Options envisagées · Décision · Conséquences*.

## Index complet

| # | Décision | Statut | Lien |
|---|---|---|---|
| [0001](./0001-clean-architecture-en-couches.md) | Architecture en couches (Clean Architecture / DDD) | ✅ Accepté | [Synthèse](./SYNTHESE-ADR.md#adr-0001--architecture-en-couches-clean-architecture--ddd) |
| [0002](./0002-domaine-independant-de-django.md) | Domaine indépendant de Django (persistence-ignorant) | ✅ Accepté | [Synthèse](./SYNTHESE-ADR.md#adr-0002--domaine-indépendant-de-django-persistence-ignorant) |
| [0003](./0003-journal-audit-vs-event-sourcing.md) | Journal d'audit = exigence métier ; ES = détail d'infra | ✅ Accepté | [Synthèse](./SYNTHESE-ADR.md#adr-0003--journal-daudit--exigence-métier--es--détail-dinfra) |
| [0004](./0004-petits-agregats-coherence-eventual.md) | Petits agrégats, référence par identité, cohérence éventuelle | ✅ Accepté | [Synthèse](./SYNTHESE-ADR.md#adr-0004--petits-agrégats-référence-par-identité-cohérence-eventual) |
| [0005](./0005-isolation-bounded-contexts.md) | Isolation stricte des bounded contexts (pas de FK ORM) | ✅ Accepté | [Synthèse](./SYNTHESE-ADR.md#adr-0005--isolation-stricte-des-bounded-contexts) |

## Guide de lecture

### 🎯 Si vous débutez
Lire **[SYNTHESE-ADR.md](./SYNTHESE-ADR.md)** — c'est une synthèse avec exemples concrets.

### ⚖️ Si vous décidez d'une nouvelle ADR
Lire un ADR existant (ex. [0001](./0001-clean-architecture-en-couches.md)) pour le format, puis créer votre ADR en respectant les sections : Statut, Contexte, Options, Décision, Conséquences.

### 🔍 Si vous challengez une décision
Ouvrir une issue (`architecture:` label) — chaque ADR a un statut, mais rien n'est gravé dans la pierre si le contexte change.

---

**Dernière mise à jour** : 2026-07-28
