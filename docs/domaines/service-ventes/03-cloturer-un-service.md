# Fonctionnalité : Clôturer un service

## Vue d'ensemble

**Domaine** : Service & Ventes  
**Acteur** : Gérante  
**Déclencheur** : Fin de service (clôture de la journée)  
**Résultat** : Service passe à statut CLÔTURÉ, ne peut plus recevoir de ventes

## Flux principal

```
Gérante clôture le service du jour
    → POST /api/services/{service_id}/cloture/
    → Charge Service (vérifier statut=OUVERT)
    → Met à jour statut → CLÔTURÉ, fixe clos_le
    → Enregistre événement ServiceCloture
    → Retourne ServiceDTO
    ✓ Service scellé, aucune modification future possible
```

## Contrats API

### Entrée (CloturerServiceCommand)

| Champ | Type | Description |
|---|---|---|
| `service_id` | str | ID du service à clôturer |
| `auteur_id` | str | ID de la gérante qui clôture |

### Sortie (ServiceDTO)

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

## Invariants

1. **État initial** : `statut == OUVERT`
   - Toute autre tentative lève `ServiceDejaCloture`

2. **Immuabilité** : une fois clôturé, le service ne peut pas être réouvert
   - Test : `test_cloturer_un_service_deja_cloture_est_interdit[cloture]`

3. **Horodatage** : `clos_le` est fixé au moment de la clôture
   - Capté précisément par `Clock.now()`

## Événement domaine produit

```
ServiceCloture
├─ service_id: str
├─ bar_id: str
└─ auteur_id: str
```

## Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | ServiceIntrouvable | Service n'existe pas |
| 409 | ServiceDejaCloture | Service déjà clôturé ou scellé |

## Garde-fou métier (à implémenter)

⚠️ **Attention** : cette fonctionnalité n'implémente **pas** le garde-fou complet défini en ADR-0004 :
- ❌ Ne vérifie pas si des `Addition` sont ouvertes
- ⚠️ Pourra être clôturé même si des clients attendent leurs additions
- ✅ Le garde-fou viendra avec l'implémentation de la fonctionnalité « Ouvrir une addition »

## Exemple local (curl)

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

# Résultat : statut → "cloture", clos_le renseigné ✓

# Tenter de clôturer à nouveau → 409
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/cloture/ \
  -H "Content-Type: application/json" \
  -d '{"auteur_id": "u1"}'
# {"detail": "Le service est déjà clôturé."}
```

## Chemins de test

- `test_service_domain.py::test_cloturer_service_met_le_statut_a_cloture` — Domaine pur
- `test_cloturer_service_handler.py::test_le_service_est_mis_a_jour_et_le_dto_est_renvoye` — Application + handler
- `test_cloturer_service_api.py::test_cloturer_service_met_le_statut_a_cloture_et_journalise` — API intégration

---

**Statut** : ✅ LIVRÉ  
**PR** : Mergée sur `main`  
**Dernier commit** : feat(service_ventes): cloturer un service
