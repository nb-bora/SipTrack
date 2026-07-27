# 📚 SipTrack — Documentation de référence

> Le registre incontestable du bar. Documentation vivante du **domaine métier**, de
> l'**architecture** et des **cas d'usage** de SipTrack.

👉 **[Commencer par l'INDEX →](./INDEX.md)**

## À quoi sert ce dossier

SipTrack est un outil de **gestion et d'audit** pour bars au Cameroun. Cette documentation
fige le fruit de la phase de *Product Discovery* : le métier, le langage commun, les règles,
l'architecture technique, et les fonctionnalités livrées. Elle est le **contrat partagé**
par les trois briques du projet (`Backend/`, `Frontend/`, `Mobile/`).

Elle doit rester **vivante** :
- Toute décision structurante nouvelle passe par un ADR (voir [`decisions/`](./decisions/))
- Tout changement de règle métier → mise à jour de [`02-modele-metier.md`](./02-modele-metier.md)
- Chaque tranche verticale livrée → documentation dans [`04-cas-dusage-service-ventes.md`](./04-cas-dusage-service-ventes.md)

## Ordre de lecture recommandé

### 🎯 Pour tous

1. **[01 — Glossaire ubiquitaire](./01-glossaire-ubiquitaire.md)** — Le **langage commun**.
   Chaque mot y a un sens unique et non négociable.
2. **[02 — Modèle métier](./02-modele-metier.md)** — Le **domaine** : acteurs, objets,
   événements, cycles de vie, invariants, règles de cohérence.
3. **[03 — Architecture backend](./03-architecture-backend.md)** — Le **blueprint technique**
   (DDD + Clean Architecture sur Python/Django).

### 🏗️ Pour contributeurs & développeurs

4. **[04 — Cas d'usage Service & Ventes](./04-cas-dusage-service-ventes.md)** — Documentation
   complète des **4 tranches livrées** : API, modèles de données, invariants, tests, erreurs,
   exemples curl, métriques.
5. **[CONTRIBUTING.md](../CONTRIBUTING.md)** — Guide complet :
   - Flux git (branches, commits Conventional Commits)
   - Checklist locale (ruff, mypy, lint-imports, pytest)
   - Critères de qualité (85% couverture, <20% duplication)
   - Structure de tranche verticale
   - Règles de code par couche

### ⚖️ Pour décideurs & architectes

6. **[decisions/](./decisions/)** — Les **décisions d'architecture** (ADR) et leur *pourquoi* :
   - [ADR-0001](./decisions/ADR-0001-ddd-clean-architecture.md) — DDD + Clean Architecture
   - [ADR-0002](./decisions/ADR-0002-event-sourcing-limite.md) — Event Sourcing limité
   - [ADR-0003](./decisions/ADR-0003-python-django.md) — Python + Django ORM
   - [ADR-0004](./decisions/ADR-0004-coherence-coordonnee.md) — Cohérence coordonnée (inter-agrégats)

## 📊 État actuel

| Élément | Statut |
|---|---|
| Modèle métier (cœur) | ✅ Validé en découverte |
| Blueprint d'architecture | ✅ Implémenté et prouvé |
| **Tranches livrées** | **✅ 4 tranches (46 tests)** |
| Pipeline CI/CD | ✅ GitHub Actions (1.5 min) |
| Qualité code | ✅ Ruff + MyPy strict + lint-imports + pip-audit |
| Prochaine étape | Régler une addition + Paiement partiel |

### ✅ Tranches livrées

1. **Ouvrir un service** — Création du service, statut `OUVERT`
2. **Enregistrer une vente** — Création de vente liée à un service
3. **Clôturer un service** — Transition `OUVERT → CLÔTURÉ`
4. **Ouvrir une addition** — Création d'addition par table

Voir [04 — Cas d'usage Service & Ventes](./04-cas-dusage-service-ventes.md) pour détails.

## Principes fondateurs (à ne jamais perdre de vue)

1. **La confiance ne se décrète pas, elle se prouve.** On ne surveille personne ; on rend
   les faits incontestables — et **personne n'échappe au journal, pas même le propriétaire**.
2. **Le journal des Mouvements est la seule vérité.** Tous les états (stock, caisse,
   créances) sont des **conséquences calculées**, jamais des données saisies.
3. **La caissière honnête est protégée** autant que le propriétaire est renseigné :
   c'est la condition de l'adoption sur le terrain.

## 🛠️ Commandes utiles

```bash
cd Backend

# Setup & tests
uv sync
uv run pytest                 # Tous les tests (46)
uv run pytest -v             # Verbose

# Quality gate (avant commit)
bash validate.sh

# Checks individuels
uv run ruff check .           # Lint
uv run ruff format .          # Format
uv run mypy .                 # Types
uv run lint-imports           # Architecture
uv run pip-audit              # Dépendances
```

## 📁 Structure du dossier docs/

```
docs/
├── README.md                          ← Vous êtes ici
├── 01-glossaire-ubiquitaire.md
├── 02-modele-metier.md
├── 03-architecture-backend.md
├── 04-cas-dusage-service-ventes.md    ← Cas d'usage livrés
└── decisions/
    ├── ADR-0001-ddd-clean-architecture.md
    ├── ADR-0002-event-sourcing-limite.md
    ├── ADR-0003-python-django.md
    └── ADR-0004-coherence-coordonnee.md
```

---

**Dernière mise à jour** : 2026-07-28 · Auteurs : Brice Devalsan + Claude Code (Community)
