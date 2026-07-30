# 🧪 Tests

Documentation des suites de tests par domaine.

## Domaines avec tests

### ✅ [Service & Ventes](./service-ventes/)

**État** : 46 tests (100% couverture domaine)  
**Niveaux** : Domaine, Handlers, API intégration  
**Durée CI/CD** : ~1.5 min

- Pyramide des tests (domaine → application → interface)
- Détail de chaque test, fichiers, assertions
- Commandes pour lancer les tests

[Voir la documentation des tests →](./service-ventes/)

---

## 📊 Métriques globales

| Métrique | Valeur |
|---|---|
| **Tests (total)** | 46 |
| **Couverture domaine** | 100% |
| **Couverture application** | 100% |
| **Couverture infrastructure** | 95% |
| **Temps CI/CD** | ~1.5 min |

---

## 🏗️ Pyramide des tests

```
Intégration (API)
    ↑
    ├─ test_*_api.py
    ├─ HTTP réel
    ├─ ~3-5 tests par fonctionnalité
    │
Application (Handlers)
    ↑
    ├─ test_*_handler.py
    ├─ Fakes en mémoire
    ├─ ~5 tests par fonctionnalité
    │
Domaine (Pur)
    ↑
    ├─ test_*_domain.py
    ├─ Python pur, 0 Django
    ├─ ~8-10 tests par agrégat
    └─ Majorité des tests
```

### Ratio recommandé

- **Domaine** : 70% (règles métier, invariants)
- **Application** : 20% (orchestration, persistance)
- **Intégration** : 10% (HTTP, contracts API)

SipTrack **suit ce ratio** : 30+ tests domaine, 15 tests app, 5 tests API.

---

## 🚀 Lancer les tests

### Tous les tests

```bash
cd Backend
uv run pytest
```

### Par niveau

```bash
# Domaine uniquement
uv run pytest contexts/*/tests/test_*_domain.py

# Handlers uniquement
uv run pytest contexts/*/tests/test_*_handler.py

# API uniquement
uv run pytest contexts/*/tests/test_*_api.py
```

### Par domaine

```bash
uv run pytest contexts/service_ventes/tests/
uv run pytest contexts/stock_inventaire/tests/
# etc.
```

### Une seule fonction

```bash
uv run pytest contexts/service_ventes/tests/test_service_domain.py::test_ouvrir_service_met_le_statut_a_ouvert -v
```

### Avec couverture

```bash
uv run pytest --cov=contexts --cov-report=html
# Ouvre htmlcov/index.html dans le navigateur
```

### Mode watch (re-lance à chaque changement de fichier)

```bash
uv run pytest-watch
```

---

## 📝 Conventions de test

### Nommage des tests

```python
# Domaine : comportement / invariant
def test_une_quantite_negative_est_rejetee():
    """Domaine : quantité > 0."""


# Handler : action exécutée + résultat
def test_la_vente_est_persistee_et_journalisee():
    """Application : orchestre création + persistance."""


# API : HTTP + contrat
def test_ouvrir_service_cree_le_service_et_retourne_201():
    """Interface : POST → 201 + DTO."""
```

### Structure d'un test

```python
def test_quelquechose():
    """Docstring courte et claire."""
    # SETUP
    obj = Class(...)
    
    # ACT
    result = obj.methode()
    
    # ASSERT
    assert result == expected
```

### Fakes en mémoire (handlers)

```python
# Pas de vraie base, pas de vraie journalisation
class FakeRepository:
    def __init__(self):
        self.storage = {}
    
    def ajouter(self, obj):
        self.storage[obj.id] = obj
    
    def par_id(self, id):
        return self.storage.get(id)
```

---

## 🔍 Points de contrôle

### Avant un commit

```bash
# Lancer les tests
uv run pytest

# Si tests verts, c'est bon ! (CI fera le reste)
```

### Sur la CI/CD

```bash
# .github/workflows/ci.yml exécute :
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run lint-imports
uv run pytest          ← Tests
uv run pip-audit       ← Sécurité des dépendances
```

---

## 📚 Références

- **Modèle métier** : [../02-modele-metier.md](../02-modele-metier.md)
- **Architecture** : [../03-architecture-backend.md](../03-architecture-backend.md)
- **Patterns tactiques** : [../decisions/SYNTHESE-ADR.md](../decisions/SYNTHESE-ADR.md)
- **Guide de contribution** : [../../CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**Dernière mise à jour** : 2026-07-28  
**Auteur** : Claude Code (Community)
