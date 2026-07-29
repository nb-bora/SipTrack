# SipTrack

[![CI](https://github.com/nb-bora/SipTrack/workflows/CI/badge.svg)](https://github.com/nb-bora/SipTrack/actions?query=workflow:CI)
[![API Status](https://img.shields.io/endpoint?url=https%3A%2F%2Fsiptrack-api.onrender.com%2Fapi%2Fdoc%2F&label=API%20Docs&color=brightgreen)](https://siptrack-api.onrender.com/api/doc/)
[![Status](https://img.shields.io/badge/Status-PoC%2FNon--prod-red)](./docs/07-audit-securite.md)

> Le registre incontestable du bar.

**Les trois blockers de sécurité sont fermés** : cloisonnement entre bars, contrôle des capacités ([ADR-0006](./docs/decisions/0006-autorisation-a-la-frontiere.md)) et idempotence des écritures ([ADR-0009](./docs/decisions/0009-idempotence-des-ecritures.md)).

⚠️ **Il n'existe pas encore d'inscription publique** : un nouvel arrivant ne peut pas créer son compte par l'API. Restent aussi sans réponse les sauvegardes, le health check et les alertes.

**SipTrack** est un outil de **gestion et d'audit** pour bars au Cameroun : il trace chaque
mouvement de stock, d'argent, de vidanges, de casiers et de créances, de façon **vérifiable et
attribuable** — même hors ligne, même quand le propriétaire n'est pas là.

---

## 🚀 **Liens importants**

| Ressource | Lien |
|---|---|
| **📚 Documentation complète** | [docs/](./docs/INDEX.md) |
| **📊 Swagger UI (API)** | [siptrack-api.onrender.com/api/doc/](https://siptrack-api.onrender.com/api/doc/) |
| **🔧 Déploiement & Infrastructure** | [docs/06-deploiement.md](./docs/06-deploiement.md) |

---

## 📂 **Structure du dépôt**

| Dossier | Rôle |
|---|---|
| [`Backend/`](./Backend/) | API (Django, DDD + Clean Architecture, **243 tests**) |
| [`Frontend/`](./Frontend/) | Application web |
| [`Mobile/`](./Mobile/) | Application mobile (offline-first) |
| [`docs/`](./docs/) | **Documentation de référence** : métier, langage, architecture, décisions |
| [`render.yaml`](./render.yaml) | Infrastructure-as-Code (Blueprint Render) |

---

## 🎯 **Pour débuter**

### 1️⃣ **Comprendre le projet**
Lire la [documentation de référence](./docs/INDEX.md) :
- [01 — Glossaire ubiquitaire](./docs/01-glossaire-ubiquitaire.md) — Vocabulaire métier
- [02 — Modèle métier](./docs/02-modele-metier.md) — Domaine, invariants
- [03 — Architecture backend](./docs/03-architecture-backend.md) — DDD + Clean Architecture

### 2️⃣ **Explorer l'API**
```bash
# API en ligne :
curl https://siptrack-api.onrender.com/api/doc/

# Ou en local (dev) :
cd Backend
uv run pytest              # Tous les tests (243)
python manage.py runserver # Démarrer le serveur
# Puis : http://localhost:8000/api/doc/
```

### 3️⃣ **Développer localement**

**Prérequis :**
- Python 3.13+
- Docker & Docker Compose (pour PostgreSQL + pgAdmin + Portainer)

**Setup :**
```bash
# 1. Base de données locale
cp .env.docker.example .env.docker
# Remplacer les mots de passe dans .env.docker
docker compose --env-file .env.docker up -d

# 2. Backend
cd Backend
uv sync                          # Installer les dépendances
python manage.py migrate         # Initialiser la base
python manage.py runserver       # Démarrer sur http://localhost:8000
```

**Outils locaux :**
- **pgAdmin** (admin DB) : http://127.0.0.1:5050
- **Portainer** (Docker UI) : https://127.0.0.1:9443

---

## 🚀 **Déploiement**

### Production (Render)

**Adresse :** https://siptrack-api.onrender.com

**Pipeline CI/CD automatique :**
```
git push (main)
  → GitHub Actions (quality gate : tests, lint, types)
    → ✓ vert → Render build & deploy
    → ✗ rouge → Rien ne se passe
```

**Configuration requise :**
1. Render → siptrack-api → Deploy Hook (secret `RENDER_DEPLOY_HOOK_URL` sur GitHub)
2. GitHub → Auto-Deploy : **"After CI Checks Pass"**

Voir [docs/06-deploiement.md](./docs/06-deploiement.md) pour la procédure complète.

### Développement local

```bash
cd Backend
uv run pytest                              # Tests (243)
uv run ruff check .                        # Lint
uv run ruff format --check .               # Format
uv run mypy .                              # Types (strict)
uv run lint-imports                        # Architecture
```

---

## 💡 **Principes fondateurs**

1. **La confiance ne se décrète pas, elle se prouve** — on rend les faits incontestables,
   et personne n'échappe au journal.
2. **Le journal des mouvements est la seule vérité** — tous les états sont calculés.
3. **La personne honnête est protégée** autant que le propriétaire est renseigné.

---

## 📊 **État du projet**

| Aspect | État |
|---|---|
| **Tests** | 243 ✓ (dont 21 de sécurité) |
| **Quality gates** | ✓ ruff, mypy strict, lint-imports, pytest |
| **CI/CD** | ✓ GitHub Actions → Render (auto) |
| **Documentation** | ✓ Complète (métier + architecture + déploiement) |
| **API** | ✓ Swagger public : https://siptrack-api.onrender.com/api/doc/ |

---

## 🔒 **À savoir avant la production**

✅ **Corrigé** — le cloisonnement entre bars et le contrôle des capacités sont
appliqués à chaque frontière HTTP ([ADR-0006](./docs/decisions/0006-autorisation-a-la-frontiere.md)).

⚠️ **Reste à faire** — **l'idempotence des écritures**. L'app mobile est
offline-first : à la reconnexion, une requête rejouée crée aujourd'hui un
doublon que le journal immuable ne peut pas défaire.

Détail dans [docs/07-audit-securite.md](./docs/07-audit-securite.md).

---

## 📝 **Contribuer**

1. Créer une branche : `git checkout -b feat/nom-feature`
2. Coder et tester
3. Push et créer une PR
4. La CI tourne automatiquement
5. Merge → redéploiement automatique sur Render

Voir [CONTRIBUTING.md](./CONTRIBUTING.md) pour le workflow complet.
