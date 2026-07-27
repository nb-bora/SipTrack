# 🧪 Tests : Service & Ventes

Documentation des suites de tests pour le domaine Service & Ventes.

## Organisation

Les tests suivent la **pyramide de tests** :

```
Intégration (API)
    ↑
Application (handlers)
    ↑
Domaine (pur)  ← Majorité
```

### Fichiers de tests

| Fichier | Niveau | Couverture | Compter |
|---|---|---|---|
| `test_service_domain.py` | Domaine | Service (création, transitions) | ~8 tests |
| `test_vente_domain.py` | Domaine | Vente (quantité, montant) | ~6 tests |
| `test_addition_domain.py` | Domaine | Addition (création, transitions) | ~4 tests |
| `test_ouvrir_service_handler.py` | Application | OuvrirServiceHandler | ~5 tests |
| `test_enregistrer_vente_handler.py` | Application | EnregistrerVenteHandler | ~5 tests |
| `test_cloturer_service_handler.py` | Application | CloturerServiceHandler | ~5 tests |
| `test_ouvrir_addition_handler.py` | Application | OuvrirAdditionHandler | ~5 tests |
| `test_ouvrir_service_api.py` | Intégration | API POST /api/services/ | ~3 tests |
| `test_enregistrer_vente_api.py` | Intégration | API POST /api/services/{id}/ventes/ | ~3 tests |
| `test_cloturer_service_api.py` | Intégration | API POST /api/services/{id}/cloture/ | ~3 tests |
| `test_ouvrir_addition_api.py` | Intégration | API POST /api/services/{id}/additions/ | ~3 tests |

**Total** : 50 tests

---

## 📚 Fonctionnalité 1 : Ouvrir un service

### Tests domaine (`test_service_domain.py`)

```python
def test_ouvrir_service_met_le_statut_a_ouvert():
    """Service démarre au statut OUVERT."""
    service = Service.ouvrir(...)
    assert service.statut == StatutService.OUVERT
```

**Invariants vérifiés** :
- ✅ Statut initial = OUVERT
- ✅ `ouvert_le` horodaté
- ✅ Événement ServiceOuvert émis
- ✅ fond_de_caisse ≥ 0

**Fichier** : [Backend/contexts/service_ventes/tests/test_service_domain.py](../../../Backend/contexts/service_ventes/tests/test_service_domain.py)

### Tests handler (`test_ouvrir_service_handler.py`)

```python
def test_le_service_est_ajoute_et_le_dto_est_renvoye():
    """Handler orchestre création + persistance + journalisation."""
    cmd = OuvrirServiceCommand(bar_id="bar1", ...)
    dto = handler.executer(cmd)
    assert dto.statut == "ouvert"
    assert repository.par_id(dto.id) is not None
```

**Couverts** :
- ✅ Repository.ajouter() appelé
- ✅ Journal.enregistrer() appelé
- ✅ UnitOfWork.commit() appelé
- ✅ Exceptions levées et propagées

**Fichier** : [Backend/contexts/service_ventes/tests/test_ouvrir_service_handler.py](../../../Backend/contexts/service_ventes/tests/test_ouvrir_service_handler.py)

### Tests API (`test_ouvrir_service_api.py`)

```python
def test_ouvrir_service_cree_le_service_et_journalise_le_mouvement():
    """Bout en bout : POST /api/services/ → service créé."""
    response = client.post("/api/services/", data={...})
    assert response.status_code == 201
    assert response.json["statut"] == "ouvert"
```

**Couverts** :
- ✅ Endpoint 201 (créé)
- ✅ ServiceDTO retourné
- ✅ Mouvement journalisé
- ✅ Erreur 400 si montant < 0

**Fichier** : [Backend/contexts/service_ventes/tests/test_ouvrir_service_api.py](../../../Backend/contexts/service_ventes/tests/test_ouvrir_service_api.py)

---

## 🧪 Fonctionnalité 2 : Enregistrer une vente

### Tests domaine (`test_vente_domain.py`)

```python
def test_une_quantite_nulle_ou_negative_est_interdite():
    """Quantité doit être > 0."""
    with pytest.raises(ValueError):
        Vente(quantite=0, ...)
    with pytest.raises(ValueError):
        Vente(quantite=-1, ...)
```

**Invariants vérifiés** :
- ✅ Quantité > 0 (obligatoire)
- ✅ Service OUVERT
- ✅ Montant = quantité × prix (calculé)
- ✅ Événement VenteEnregistree émis

**Fichier** : [Backend/contexts/service_ventes/tests/test_vente_domain.py](../../../Backend/contexts/service_ventes/tests/test_vente_domain.py)

### Tests handler (`test_enregistrer_vente_handler.py`)

```python
def test_la_vente_est_persistee_journalisee_purgee_et_commitee():
    """Orchestration complète."""
    cmd = EnregistrerVenteCommand(...)
    dto = handler.executer(cmd)
    assert repository.par_id(dto.id) is not None
    assert journal.evenements[-1].type == "VenteEnregistree"
```

**Couverts** :
- ✅ Repository.ajouter() appelé
- ✅ Journal.enregistrer() appelé
- ✅ UnitOfWork.commit() appelé
- ✅ Exceptions (ServiceIntrouvable, ServiceNonOuvert)

**Fichier** : [Backend/contexts/service_ventes/tests/test_enregistrer_vente_handler.py](../../../Backend/contexts/service_ventes/tests/test_enregistrer_vente_handler.py)

### Tests API (`test_enregistrer_vente_api.py`)

```python
def test_enregistrer_une_vente_cree_la_vente_et_journalise():
    """Bout en bout : POST /api/services/{id}/ventes/ → vente créée."""
    response = client.post(f"/api/services/{service_id}/ventes/", data={...})
    assert response.status_code == 201
    assert response.json["montant_total"] == 1300
```

**Couverts** :
- ✅ Endpoint 201 (créé)
- ✅ VenteDTO retourné
- ✅ Montant calculé
- ✅ Erreur 404 si service inexistant
- ✅ Erreur 409 si service fermé

**Fichier** : [Backend/contexts/service_ventes/tests/test_enregistrer_vente_api.py](../../../Backend/contexts/service_ventes/tests/test_enregistrer_vente_api.py)

---

## 🧪 Fonctionnalité 3 : Clôturer un service

### Tests domaine (`test_service_domain.py`)

```python
def test_cloturer_service_met_le_statut_a_cloture():
    """Service passe à CLÔTURÉ."""
    service = Service.ouvrir(...)
    service.cloturer(auteur_id="u1", horodatage=now)
    assert service.statut == StatutService.CLOTURE
```

**Invariants vérifiés** :
- ✅ Transition OUVERT → CLÔTURÉ
- ✅ `clos_le` horodaté
- ✅ Événement ServiceCloture émis
- ✅ Double clôture interdite (levé ServiceDejaCloture)

**Fichier** : [Backend/contexts/service_ventes/tests/test_service_domain.py](../../../Backend/contexts/service_ventes/tests/test_service_domain.py)

### Tests handler (`test_cloturer_service_handler.py`)

```python
def test_le_service_est_mis_a_jour_et_le_dto_est_renvoye():
    """Handler orchestre transition + persistance + journalisation."""
    cmd = CloturerServiceCommand(service_id=..., auteur_id=...)
    dto = handler.executer(cmd)
    assert dto.statut == "cloture"
    assert dto.clos_le is not None
```

**Couverts** :
- ✅ Repository.mettre_a_jour() appelé
- ✅ Journal.enregistrer() appelé
- ✅ UnitOfWork.commit() appelé
- ✅ Exception ServiceDejaCloture propagée

**Fichier** : [Backend/contexts/service_ventes/tests/test_cloturer_service_handler.py](../../../Backend/contexts/service_ventes/tests/test_cloturer_service_handler.py)

### Tests API (`test_cloturer_service_api.py`)

```python
def test_cloturer_service_met_le_statut_a_cloture_et_journalise():
    """Bout en bout : POST /api/services/{id}/cloture/ → service clôturé."""
    response = client.post(f"/api/services/{service_id}/cloture/", data={...})
    assert response.status_code == 200
    assert response.json["statut"] == "cloture"
```

**Couverts** :
- ✅ Endpoint 200 (succès)
- ✅ ServiceDTO retourné
- ✅ Erreur 404 si service inexistant
- ✅ Erreur 409 si déjà clôturé

**Fichier** : [Backend/contexts/service_ventes/tests/test_cloturer_service_api.py](../../../Backend/contexts/service_ventes/tests/test_cloturer_service_api.py)

---

## 🧪 Fonctionnalité 4 : Ouvrir une addition

### Tests domaine (`test_addition_domain.py`)

```python
def test_ouvrir_addition_met_le_statut_a_ouverte():
    """Addition démarre au statut OUVERTE."""
    addition = Addition.ouvrir(table_numero=5, ...)
    assert addition.statut == StatutAddition.OUVERTE
```

**Invariants vérifiés** :
- ✅ Statut initial = OUVERTE
- ✅ `ouvert_le` horodaté
- ✅ table_numero valide (≥ 1)
- ✅ Événement AdditionOuverte émis

**Fichier** : [Backend/contexts/service_ventes/tests/test_addition_domain.py](../../../Backend/contexts/service_ventes/tests/test_addition_domain.py)

### Tests handler (`test_ouvrir_addition_handler.py`)

```python
def test_l_addition_est_ajoutee_et_le_dto_est_renvoye():
    """Handler orchestre création + persistance + journalisation."""
    cmd = OuvrirAdditionCommand(service_id=..., table_numero=5)
    dto = handler.executer(cmd)
    assert dto.statut == "ouverte"
```

**Couverts** :
- ✅ Repository.ajouter() appelé
- ✅ Journal.enregistrer() appelé
- ✅ UnitOfWork.commit() appelé
- ✅ Exceptions levées

**Fichier** : [Backend/contexts/service_ventes/tests/test_ouvrir_addition_handler.py](../../../Backend/contexts/service_ventes/tests/test_ouvrir_addition_handler.py)

### Tests API (`test_ouvrir_addition_api.py`)

```python
def test_ouvrir_addition_cree_l_addition_et_journalise():
    """Bout en bout : POST /api/services/{id}/additions/ → addition créée."""
    response = client.post(f"/api/services/{service_id}/additions/", data={...})
    assert response.status_code == 201
    assert response.json["table_numero"] == 5
```

**Couverts** :
- ✅ Endpoint 201 (créé)
- ✅ AdditionDTO retourné
- ✅ Erreur 404 si service inexistant
- ✅ Erreur 409 si service fermé
- ✅ Erreur 400 si table_numero < 1

**Fichier** : [Backend/contexts/service_ventes/tests/test_ouvrir_addition_api.py](../../../Backend/contexts/service_ventes/tests/test_ouvrir_addition_api.py)

---

## 🏃 Lancer les tests

```bash
cd Backend

# Tous les tests
uv run pytest

# Verbose
uv run pytest -v

# Domaine uniquement
uv run pytest contexts/service_ventes/tests/test_*_domain.py

# Handlers uniquement
uv run pytest contexts/service_ventes/tests/test_*_handler.py

# API uniquement
uv run pytest contexts/service_ventes/tests/test_*_api.py

# Une seule fonction
uv run pytest contexts/service_ventes/tests/test_service_domain.py::test_ouvrir_service_met_le_statut_a_ouvert

# Avec couverture
uv run pytest --cov=contexts/service_ventes
```

## 📊 Couverture

```bash
uv run pytest --cov=contexts/service_ventes --cov-report=html
# Ouvre htmlcov/index.html dans le navigateur
```

---

**Dernière mise à jour** : 2026-07-28  
**Auteur** : Claude Code (Community)
