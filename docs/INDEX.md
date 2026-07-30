# 📚 Documentation SipTrack — Index principal

Bienvenue ! Cette documentation est organisée par **domaines métier** et **tests associés**.

## 🗺️ Navigation

### 📖 Fondamentaux (lire en premier)

- **[01 — Glossaire ubiquitaire](./01-glossaire-ubiquitaire.md)** — Langage commun de SipTrack
- **[02 — Modèle métier](./02-modele-metier.md)** — Domaine, agrégats, invariants
- **[03 — Architecture backend](./03-architecture-backend.md)** — DDD + Clean Architecture
- **[06 — Déploiement et outillage](./06-deploiement.md)** — Render, CI/CD, pgAdmin, Portainer
- **[07 — Audit de sécurité](./07-audit-securite.md)** — **⚠️ Blocker restant avant production**

### 🎨 Frontend & Harmonisation

- **[09 — Harmonisation Frontend ↔ Backend](./09-harmonisation-frontend-backend.md)** — Contrat API, corrections, state of the art
- **[10 — Backend : lacunes et priorité](./10-backend-lacunes-priorite.md)** — 3 trous connus (CORS, query services), comment les corriger
- **[11 — Audit alignement : PARFAIT ✅](./11-audit-alignement-parfait.md)** — Vérification pointilliste de tous les 32 endpoints

### 🏢 Domaines métier

Chaque domaine a sa propre documentation, organisée par **fonctionnalité** :

#### [Domaine : Service & Ventes](./domaines/service-ventes/)

Gestion des services, ventes, additions et règlements de tables.

| Fonctionnalité | Statut | Doc |
|---|---|---|
| 1. Ouvrir un service | ✅ LIVRÉ | [Lire](./domaines/service-ventes/01-ouvrir-un-service.md) |
| 2. Enregistrer une vente | ✅ LIVRÉ | [Lire](./domaines/service-ventes/02-enregistrer-une-vente.md) |
| 3. Clôturer un service | ✅ LIVRÉ | [Lire](./domaines/service-ventes/03-cloturer-un-service.md) |
| 4. Ouvrir une addition | ✅ LIVRÉ | [Lire](./domaines/service-ventes/04-ouvrir-une-addition.md) |

[Vue d'ensemble du domaine →](./domaines/service-ventes/)

---

### 🧪 Tests

Chaque domaine a une suite de tests organisée par niveau (domaine, application, intégration) :

#### [Tests : Service & Ventes](./tests/service-ventes/)

- 46 tests répartis sur 3 niveaux
- 100% couverture domaine
- ~1.5 min en CI/CD

[Documentation des tests →](./tests/service-ventes/)

---

### ⚖️ Architecture & Décisions

- **[decisions/](./decisions/)** — ADRs (Architecture Decision Records)
  - [SYNTHESE-ADR.md](./decisions/SYNTHESE-ADR.md) — Résumé avec exemples concrets
  - [ADR-0001](./decisions/0001-clean-architecture-en-couches.md) — 4 couches (Clean Architecture)
  - [ADR-0002](./decisions/0002-domaine-independant-de-django.md) — Domaine pur
  - [ADR-0003](./decisions/0003-journal-audit-vs-event-sourcing.md) — Journal d'audit
  - [ADR-0004](./decisions/0004-petits-agregats-coherence-eventual.md) — Petits agrégats
  - [ADR-0005](./decisions/0005-isolation-bounded-contexts.md) — Isolation des contextes
  - [ADR-0006](./decisions/0006-autorisation-a-la-frontiere.md) — Autorisation à la frontière
  - [ADR-0007](./decisions/0007-comptes-plateforme.md) — Comptes plateforme : lire, jamais écrire
  - [ADR-0008](./decisions/0008-observabilite.md) — Observabilité : ce qui casse, sans les données
  - [ADR-0009](./decisions/0009-idempotence-des-ecritures.md) — Idempotence : un rejeu, un seul fait
  - [ADR-0010](./decisions/0010-durcissement-securite.md) — Clé de repli, débit, jetons, hachage

---

## 🎯 Cas d'usage courants

### Je veux intégrer le frontend avec le backend

1. Lire [09 — Harmonisation Frontend ↔ Backend](./09-harmonisation-frontend-backend.md) — Contrat exact, état de conformité
2. Consulter [10 — Backend : lacunes et priorité](./10-backend-lacunes-priorite.md) — Ce qu'il faut corriger et par où commencer
3. Mettre en place CORS sur le backend
4. Lancer le test basique (voir doc 09)

### Je veux comprendre une fonctionnalité

1. Lire la doc de la fonctionnalité dans `domaines/<domaine>/`
2. Consulter les exemples curl
3. Parcourir les tests associés dans `tests/<domaine>/`

**Exemple** : Comprendre « Enregistrer une vente »
1. [domaines/service-ventes/02-enregistrer-une-vente.md](./domaines/service-ventes/02-enregistrer-une-vente.md)
2. Tests : [tests/service-ventes/README.md](./tests/service-ventes/) → Fonctionnalité 2

### Je veux développer une nouvelle fonctionnalité

1. Lire [CONTRIBUTING.md](../CONTRIBUTING.md) — Workflow complet
2. Choisir un domaine dans `domaines/`
3. Créer une nouvelle tranche verticale (domaine → application → infrastructure → interface)
4. Ajouter des tests (domaine → handler → API)
5. Créer une doc dans `domaines/<domaine>/0X-nom.md`

### Je veux auditer l'architecture

1. Lire [decisions/SYNTHESE-ADR.md](./decisions/SYNTHESE-ADR.md) — Résumé + exemples
2. Lancer `uv run lint-imports` — Vérifie les contrats d'architecture
3. Consulter les ADRs complets dans `decisions/`

### Je suis nouveau sur le projet

1. Lire [01 — Glossaire ubiquitaire](./01-glossaire-ubiquitaire.md) — Vocabulaire
2. Lire [02 — Modèle métier](./02-modele-metier.md) — Domaine complet
3. Lire [03 — Architecture backend](./03-architecture-backend.md) — Structure technique
4. Explorer une fonctionnalité livrée dans [domaines/service-ventes/](./domaines/service-ventes/)
5. Lancer les tests : `cd Backend && uv run pytest`

---

## 📊 État du projet

| Élément | Statut |
|---|---|
| **Fonctionnalités (Service & Ventes)** | 4 livrées, 4 prévues |
| **Tests** | 46 (100% couverture domaine) |
| **Pipeline CI/CD** | ✅ GitHub Actions (~1.5 min) |
| **Qualité** | ✅ Ruff + MyPy strict + lint-imports |
| **Documentation** | ✅ Complète par fonctionnalité |

---

## 📝 Convention de documentation

Chaque fonctionnalité a sa propre doc avec sections standardisées :

```markdown
# Fonctionnalité : [Nom]

## Vue d'ensemble
(Contexte métier)

## Flux principal
(Diagramme ASCII)

## Contrats API
(Entrée/Sortie)

## Invariants
(Règles métier)

## Événement domaine produit
(Event sourcing)

## Erreurs possibles
(HTTP codes)

## Exemple local (curl)
(Copier-coller prêt)

## Chemins de test
(Où trouver les tests)
```

---

## 🛠️ Commandes utiles

```bash
cd Backend

# Tests
uv run pytest                    # Tous (46 tests)
uv run pytest -v               # Verbose

# Quality gate
bash validate.sh                # Lint + format + types + archi + tests

# Checks individuels
uv run ruff check .             # Lint
uv run mypy .                   # Types
uv run lint-imports             # Architecture
uv run pip-audit                # Dépendances
```

---

## 📂 Structure complète

```
docs/
├── INDEX.md                           ← Vous êtes ici
├── 01-glossaire-ubiquitaire.md
├── 02-modele-metier.md
├── 03-architecture-backend.md
├── 06-deploiement.md
├── 07-audit-securite.md               (⚠️ LIRE AVANT PROD)
├── 09-harmonisation-frontend-backend.md
├── 10-backend-lacunes-priorite.md
│
├── domaines/
│   └── service-ventes/
│       ├── README.md                  (vue d'ensemble du domaine)
│       ├── 01-ouvrir-un-service.md
│       ├── 02-enregistrer-une-vente.md
│       ├── 03-cloturer-un-service.md
│       └── 04-ouvrir-une-addition.md
│
├── tests/
│   └── service-ventes/
│       └── README.md                  (documentation des tests)
│
└── decisions/
    ├── README.md
    ├── SYNTHESE-ADR.md
    ├── 0001-clean-architecture-en-couches.md
    ├── 0002-domaine-independant-de-django.md
    ├── 0003-journal-audit-vs-event-sourcing.md
    ├── 0004-petits-agregats-coherence-eventual.md
    ├── 0005-isolation-bounded-contexts.md
    ├── 0006-autorisation-a-la-frontiere.md
    ├── 0007-comptes-plateforme.md
    ├── 0008-observabilite.md
    ├── 0009-idempotence-des-ecritures.md
    └── 0010-durcissement-securite.md
```

---

## 📞 Support

- **Questions d'architecture** → Consulter [decisions/SYNTHESE-ADR.md](./decisions/SYNTHESE-ADR.md)
- **Questions métier** → Lire [02 — Modèle métier](./02-modele-metier.md)
- **Questions sur une fonctionnalité** → Lire la doc dans `domaines/<domaine>/`
- **Questions sur les tests** → Lire [tests/<domaine>/README.md](./tests/service-ventes/)
- **Bugs ou améliorations** → Ouvrir une issue GitHub

---

**Version** : 2026-07-28  
**Auteur** : Claude Code (Community)
