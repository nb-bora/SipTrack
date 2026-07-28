# Fonctionnalité : Régler une addition

## Vue d'ensemble

**Domaine** : Service & Ventes  
**Acteur** : Serveuse  
**Déclencheur** : Client paie l'addition  
**Résultat** : Addition passe à statut RÉGLÉE, immuable

## Flux principal

```
Serveuse règle l'addition de la table 5
    → POST /api/services/{id}/additions/{id}/reglement/
    → Charge Addition (vérifier statut=OUVERTE)
    → Met à jour statut → RÉGLÉE, fixe ferme_le
    → Enregistre événement AdditionReglee
    → Retourne AdditionDTO
    ✓ Addition scellée, aucune modification possible
```

## Contrats API

### Entrée (ReglementAdditionCommand)

| Champ | Type | Description |
|---|---|---|
| `service_id` | str | ID du service (chemin) |
| `addition_id` | str | ID de l'addition (chemin) |
| `auteur_id` | str | ID de la serveuse |

### Sortie (AdditionDTO)

```json
{
  "id": "add-789ghi",
  "service_id": "svc-123abc",
  "table_numero": 5,
  "statut": "reglee",
  "ouvert_le": "2026-07-28T10:15:00Z",
  "ferme_le": "2026-07-28T22:30:00Z"
}
```

## Invariants

1. **État initial** : `statut == OUVERTE`
   - Toute autre tentative lève `AdditionDejaCloturee`

2. **Immutabilité** : une fois réglée, l'addition ne peut plus être modifiée
   - Transition : OUVERTE → RÉGLÉE (terminal)

3. **Horodatage** : `ferme_le` est fixé au moment du règlement
   - Capté précisément par `Clock.now()`

## Événement domaine produit

```
AdditionReglee
├─ addition_id: str
├─ service_id: str
├─ table_numero: int
└─ auteur_id: str
```

## Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | AdditionIntrouvable | Addition n'existe pas |
| 409 | AdditionDejaCloturee | Addition déjà réglée ou abandonnée |

## Exemple local (curl)

```bash
# Ouvrir un service
SERVICE_ID=$(curl -s -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -d '{"bar_id":"bar1","auteur_id":"u1","capacite":"operatrice","fond_de_caisse":10000}' \
  | jq -r '.id')

# Ouvrir une addition
ADDITION_ID=$(curl -s -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/additions/ \
  -H "Content-Type: application/json" \
  -d '{"auteur_id":"u1","table_numero":5}' \
  | jq -r '.id')

# Régler l'addition
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/additions/$ADDITION_ID/reglement/ \
  -H "Content-Type: application/json" \
  -d '{"auteur_id": "u1"}'
```

Résultat :
```json
{
  "id": "add-def456",
  "service_id": "svc-abc123",
  "table_numero": 5,
  "statut": "reglee",
  "ouvert_le": "2026-07-28T10:15:00Z",
  "ferme_le": "2026-07-28T22:30:00Z"
}
```

## Chemins de test

- `test_addition_domain.py` — Tests domaine (statut, événement, double-règlement)
- `test_regler_addition_handler.py` — Tests handler (persistance, journalisation)
- `test_regler_addition_api.py` — Tests API (codes HTTP, mouvement)

## Composition verticale

| Couche | Fichiers |
|---|---|
| **Domaine** | `domain/addition.py::Addition.regler()` |
| **Application** | `application/use_cases/regler_addition.py` |
| **Infrastructure** | `persistence/repository.py::mettre_a_jour()` |
| **Interface** | `interface/rest/views.py::ReglementAdditionView` |

## Implémentation complète

✅ Domaine : Addition.regler() — 7 tests  
✅ Application : ReglementAdditionHandler — 4 tests  
✅ Infrastructure : mapper + repository  
✅ Interface : POST /api/services/{id}/additions/{id}/reglement/  
✅ Tests : 3 tests API E2E  
✅ Documentation : cette page

---

**Statut** : ✅ LIVRÉ (branche `feat/regler-addition`)  
**Tests** : 14 total (7 domaine + 4 handler + 3 API)  
**Quality Gate** : Ruff ✓ + MyPy ✓ + lint-imports ✓  
**Dernière mise à jour** : 2026-07-28
