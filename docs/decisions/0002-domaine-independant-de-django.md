# ADR-0002 — Domaine indépendant de Django (persistence-ignorant)

- **Statut** : ✅ Accepté — 2026-07-24
- **Contexte** : Django est nativement *Active Record* (l'ORM soude modèle et persistance).
  Le DDD veut un domaine ignorant de la base. Il faut réconcilier les deux.

## Options envisagées

1. **Utiliser les modèles Django comme modèle de domaine** — simple, mais soude la logique à
   l'ORM ; casse les invariants dès qu'on manipule les modèles ailleurs ; tests lents.
2. **Domaine en Python pur + modèles ORM séparés, mapping dans le repository** — approche de
   *Architecture Patterns with Python* (annexe Django). Plus de mapping, mais domaine pur.
3. **Abandonner l'ORM** (SQL brut / autre) — perte des atouts Django (migrations, admin) sans
   bénéfice suffisant.

## Décision

Option 2. **Le domaine est du Python pur et n'importe jamais Django.** Les modèles ORM vivent
dans `infrastructure/django_app/` ; un **repository** (interface au domaine, implémentation en
infra) traduit domaine ↔ ORM via un *mapper* explicite.

## Conséquences

- ➕ Domaine testable sans Django ; règles protégées.
- ➕ Django reste un **détail** remplaçable, confiné à l'infra/interface.
- ➖ Coût de mapping domaine↔ORM et perte de raccourcis (ModelForms, ModelSerializer, admin sur
   les agrégats). Accepté.
- **Vérifié** par `import-linter` : `contexts.*.domain` ⊄ `django`.
