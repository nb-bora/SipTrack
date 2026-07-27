# 04 — Cas d'usage « Service & Ventes »

Documentation complète des fonctionnalités implémentées dans le bounded context `service_ventes`.

## Vue d'ensemble

Le contexte `service_ventes` gère :
- **Cycle de vie du Service** : ouverture, clôture, scellement
- **Enregistrement des Ventes** : création de ventes liées à un service
- **Gestion des Additions** : groupage des ventes par table

État : **3 tranches verticales livrées** + **1 en cours**

---

## Tranche 1 : Ouvrir un service

### Cas d'usage
**Acteur** : Gérante  
**Déclencheur** : Démarrage de l'activité du jour  
**Résultat** : Un nouveau service est créé et prêt à recevoir des ventes

### Flux principal

```
Gérante veut ouvrir un service
    → POST /api/services/
    → Crée agrégat Service (statut=OUVERT)
    → Enregistre événement ServiceOuvert
    → Retourne ServiceDTO avec id + statut + horodatage
    ✓ Service prêt à accueillir des ventes
```

### Entrées (OuvrirServiceCommand)

| Champ | Type | Description |
|---|---|---|
| `bar_id` | str | Identifiant du bar |
| `auteur_id` | str | Identifiant de la gérante |
| `capacite` | str | Rôle (ex. "operatrice") |
| `fond_de_caisse` | int | Capital de démarrage (XAF) |

### Sorties (ServiceDTO)

```json
{
  "id": "svc-123abc",
  "bar_id": "bar1",
  "statut": "ouvert",
  "fond_de_caisse": 10000,
  "ouvert_le": "2026-07-28T10:00:00Z",
  "clos_le": null
}
```

### Invariants

- Montant `fond_de_caisse` ≥ 0
- Attribution unique : une seule gérante par service
- Un service démarre toujours au statut `OUVERT`

### Événements produits

```
ServiceOuvert
├─ service_id: str
├─ bar_id: str
├─ auteur_id: str
└─ fond_de_caisse: int (montant en XAF)
```

### Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 400 | ValueError | Montant < 0 |
| 500 | SystemError | Impossible de générer un ID unique |

### Test & déploiement

**Local** :
```bash
curl -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -d '{
    "bar_id": "bar1",
    "auteur_id": "u1",
    "capacite": "operatrice",
    "fond_de_caisse": 10000
  }'
```

**Tests automatisés** :
- `test_service_domain.py::test_ouvrir_service_met_le_statut_a_ouvert` (domaine)
- `test_ouvrir_service_handler.py` (application + handler)
- `test_ouvrir_service_api.py::test_ouvrir_service_cree_le_service_et_journalise_le_mouvement` (API)

---

## Tranche 2 : Enregistrer une vente

### Cas d'usage
**Acteur** : Serveuse  
**Déclencheur** : Une table consomme un produit  
**Résultat** : La vente est enregistrée et liée au service

### Flux principal

```
Serveuse vend une 33 Export à la table 5
    → POST /api/services/{service_id}/ventes/
    → Charge Service (vérifier statut=OUVERT)
    → Crée agrégat Vente (montant = quantité × prix)
    → Enregistre événement VenteEnregistree
    → Retourne VenteDTO
    ✓ Vente comptabilisée, argent attribuable
```

### Entrées (EnregistrerVenteCommand)

| Champ | Type | Description |
|---|---|---|
| `service_id` | str | ID du service actif |
| `auteur_id` | str | ID de la serveuse |
| `produit_id` | str | ID du produit (ex. "33export") |
| `quantite` | int | Nombre d'unités |
| `prix_unitaire` | int | Prix en XAF |
| `forme_paiement` | str | Mode : "especes", "mobile_money", "credit" |

### Sorties (VenteDTO)

```json
{
  "id": "vente-456def",
  "service_id": "svc-123abc",
  "produit_id": "33export",
  "quantite": 2,
  "prix_unitaire": 650,
  "montant_total": 1300,
  "forme_paiement": "especes"
}
```

### Invariants

1. **Quantité strictement positive** : `quantite > 0`
   - Teste : `test_une_quantite_nulle_ou_negative_est_interdite`
   - Lève : `ValueError`

2. **Service ouvert** : ne peut vendre que si `service.statut == OUVERT`
   - Lève : `ServiceNonOuvert` (409 Conflict)

3. **Montant total** = `quantite × prix_unitaire` (calculé, jamais saisi)

### Événements produits

```
VenteEnregistree
├─ vente_id: str
├─ service_id: str
├─ produit_id: str
├─ quantite: int
├─ prix_unitaire: int (XAF)
├─ montant_total: int (XAF, calculé)
├─ forme_paiement: str
└─ auteur_id: str
```

### Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | ServiceIntrouvable | Service n'existe pas |
| 409 | ServiceNonOuvert | Service clôturé ou scellé |
| 400 | ValueError | Quantité ≤ 0 |

### Test & déploiement

**Local** :
```bash
# D'abord ouvrir un service
SERVICE_ID=$(curl -s -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -d '{"bar_id":"bar1","auteur_id":"u1","capacite":"operatrice","fond_de_caisse":10000}' \
  | jq -r '.id')

# Puis enregistrer une vente
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/ventes/ \
  -H "Content-Type: application/json" \
  -d '{
    "auteur_id": "u1",
    "produit_id": "33export",
    "quantite": 2,
    "prix_unitaire": 650,
    "forme_paiement": "especes"
  }'
```

**Tests automatisés** :
- `test_vente_domain.py::test_enregistrer_une_vente_emet_l_evenement` (domaine)
- `test_enregistrer_vente_handler.py::test_la_vente_est_persistee_journalisee_purgee_et_commitee` (app)
- `test_enregistrer_vente_api.py::test_enregistrer_une_vente_cree_la_vente_et_journalise` (API)

---

## Tranche 3 : Clôturer un service

### Cas d'usage
**Acteur** : Gérante  
**Déclencheur** : Fin de service (clôture de la journée)  
**Résultat** : Service passe à statut CLÔTURÉ, ne peut plus recevoir de ventes

### Flux principal

```
Gérante clôture le service du jour
    → POST /api/services/{service_id}/cloture/
    → Charge Service (vérifier statut=OUVERT)
    → Met à jour statut → CLÔTURÉ, fixe clos_le
    → Enregistre événement ServiceCloture
    → Retourne ServiceDTO
    ✓ Service scellé, aucune modification future possible
```

### Entrées (CloturerServiceCommand)

| Champ | Type | Description |
|---|---|---|
| `service_id` | str | ID du service à clôturer |
| `auteur_id` | str | ID de la gérante qui clôture |

### Sorties (ServiceDTO)

```json
{
  "id": "svc-123abc",
  "bar_id": "bar1",
  "statut": "cloture",
  "fond_de_caisse": 10000,
  "ouvert_le": "2026-07-28T10:00:00Z",
  "clos_le": "2026-07-28T22:30:00Z"
}
```

### Invariants

1. **État initial** : `statut == OUVERT`
   - Toute autre tentative lève `ServiceDejaCloture`

2. **Immuabilité** : une fois clôturé, le service ne peut pas être réouvert
   - Test : `test_cloturer_un_service_deja_cloture_est_interdit[cloture]`

3. **Horodatage** : `clos_le` est fixé au moment de la clôture
   - Capté précisément par `Clock.now()`

### Événements produits

```
ServiceCloture
├─ service_id: str
├─ bar_id: str
└─ auteur_id: str
```

### Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | ServiceIntrouvable | Service n'existe pas |
| 409 | ServiceDejaCloture | Service déjà clôturé ou scellé |

### Points de contrôle

**Attention** : cette tranche n'implémente **pas** le garde-fou métier (ADR-0004) :
- ❌ Ne vérifie pas si des `Addition` sont ouvertes
- ⚠️ Pourra être clôturé même si des clients attendent leurs additions
- ✅ Le garde-fou viendra avec l'implémentation de l'agrégat `Addition`

### Test & déploiement

**Local** :
```bash
# Ouvrir un service
SERVICE_ID=$(curl -s -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -d '{"bar_id":"bar1","auteur_id":"u1","capacite":"operatrice","fond_de_caisse":10000}' \
  | jq -r '.id')

# Clôturer le service
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/cloture/ \
  -H "Content-Type: application/json" \
  -d '{"auteur_id": "u1"}'

# Tenter de clôturer à nouveau → 409
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/cloture/ \
  -H "Content-Type: application/json" \
  -d '{"auteur_id": "u1"}'
# {"detail": "Le service est déjà clôturé."}
```

**Tests automatisés** :
- `test_service_domain.py::test_cloturer_service_met_le_statut_a_cloture` (domaine)
- `test_cloturer_service_handler.py::test_le_service_est_mis_a_jour_et_le_dto_est_renvoye` (app)
- `test_cloturer_service_api.py::test_cloturer_service_met_le_statut_a_cloture_et_journalise` (API)

---

## Tranche 4 : Ouvrir une addition

### Cas d'usage
**Acteur** : Serveuse  
**Déclencheur** : Arrivée d'une nouvelle table  
**Résultat** : Une nouvelle addition est créée pour la table

### Flux principal

```
Serveuse ouvre une addition pour la table 5
    → POST /api/services/{service_id}/additions/
    → Charge Service (vérifier statut=OUVERT)
    → Crée agrégat Addition (statut=OUVERTE)
    → Enregistre événement AdditionOuverte
    → Retourne AdditionDTO
    ✓ Addition prête à recevoir des ventes
```

### Entrées (OuvrirAdditionCommand)

| Champ | Type | Description |
|---|---|---|
| `service_id` | str | ID du service actif |
| `auteur_id` | str | ID de la serveuse |
| `table_numero` | int | Numéro de la table (≥ 1) |

### Sorties (AdditionDTO)

```json
{
  "id": "add-789ghi",
  "service_id": "svc-123abc",
  "table_numero": 5,
  "statut": "ouverte",
  "ouvert_le": "2026-07-28T10:15:00Z",
  "ferme_le": null
}
```

### Invariants

1. **Service ouvert** : `service.statut == OUVERT`
   - Lève : `ServiceNonOuvert`

2. **Table valide** : `table_numero ≥ 1`
   - Validé dans le serializer

3. **Statut initial** : toujours `OUVERTE`

### Événements produits

```
AdditionOuverte
├─ addition_id: str
├─ service_id: str
├─ table_numero: int
└─ auteur_id: str
```

### Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | ServiceIntrouvable | Service n'existe pas |
| 409 | ServiceNonOuvert | Service clôturé ou scellé |
| 400 | ValidationError | table_numero < 1 |

### Test & déploiement

**Local** :
```bash
# Ouvrir un service
SERVICE_ID=$(curl -s -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -d '{"bar_id":"bar1","auteur_id":"u1","capacite":"operatrice","fond_de_caisse":10000}' \
  | jq -r '.id')

# Ouvrir une addition
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/additions/ \
  -H "Content-Type: application/json" \
  -d '{
    "auteur_id": "u1",
    "table_numero": 5
  }'
```

**Tests automatisés** :
- `test_addition_domain.py::test_ouvrir_addition_met_le_statut_a_ouverte` (domaine)
- `test_ouvrir_addition_handler.py::test_l_addition_est_ajoutee_et_le_dto_est_renvoye` (app)
- `test_ouvrir_addition_api.py::test_ouvrir_addition_cree_l_addition_et_journalise` (API)

---

## État du développement

### ✅ Livré

| Tranche | Branch | PR | Status |
|---|---|---|---|
| Ouvrir un service | `feat/ouvrir-service` | Mergée | ✅ LIVRÉ |
| Enregistrer une vente | `feat/enregistrer-vente` | Mergée | ✅ LIVRÉ |
| Clôturer un service | `feat/cloturer-service` | Mergée | ✅ LIVRÉ |
| Ouvrir une addition | `feat/addition` | #7 | ✅ LIVRÉ |

### 📊 Métriques

| Métrique | Valeur |
|---|---|
| Tests (total) | 46 |
| Couverture domaine | 100% |
| Temps CI/CD | ~1.5min |
| Linting | ✓ Ruff |
| Typage | ✓ MyPy strict |
| Architecture | ✓ Import-linter |

### 🚀 Prochaines tranches prévues

1. **Régler une addition** : transition `Ouverte → Réglée`
2. **Paiement partiel** : gestion des paiements partiels
3. **Crédit** : modèle `Credit` pour les clients
4. **Sous-caisse serveuse** : réconciliation par serveuse

---

## Guide de lecture

- **Pour comprendre le métier** : lire [02-modele-metier.md](02-modele-metier.md)
- **Pour comprendre l'archi** : lire [03-architecture-backend.md](03-architecture-backend.md)
- **Pour développer une nouvelle tranche** : lire [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Pour auditer l'archi** : voir `lint-imports` dans `pyproject.toml`

---

**Dernier update** : 2026-07-28  
**Auteur** : Claude Code (Community)
