# Fonctionnalité : Enregistrer une vente

## Vue d'ensemble

**Domaine** : Service & Ventes  
**Acteur** : Serveuse  
**Déclencheur** : Une table consomme un produit  
**Résultat** : La vente est enregistrée et liée au service

## Flux principal

```
Serveuse vend une 33 Export à la table 5
    → POST /api/services/{service_id}/ventes/
    → Charge Service (vérifier statut=OUVERT)
    → Crée agrégat Vente (montant = quantité × prix)
    → Enregistre événement VenteEnregistree
    → Retourne VenteDTO
    ✓ Vente comptabilisée, argent attribuable
```

## Contrats API

### Entrée (EnregistrerVenteCommand)

| Champ | Type | Description |
|---|---|---|
| `service_id` | str | ID du service actif |
| `auteur_id` | str | ID de la serveuse |
| `produit_id` | str | ID du produit (ex. "33export") |
| `quantite` | int | Nombre d'unités |
| `prix_unitaire` | int | Prix en XAF |
| `forme_paiement` | str | Mode : "especes", "mobile_money", "credit" |

### Sortie (VenteDTO)

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

## Invariants

1. **Quantité strictement positive** : `quantite > 0`
   - Teste : `test_une_quantite_nulle_ou_negative_est_interdite`
   - Lève : `ValueError`

2. **Service ouvert** : ne peut vendre que si `service.statut == OUVERT`
   - Lève : `ServiceNonOuvert` (409 Conflict)

3. **Montant total** = `quantite × prix_unitaire` (calculé, jamais saisi)

## Événement domaine produit

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

## Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | ServiceIntrouvable | Service n'existe pas |
| 409 | ServiceNonOuvert | Service clôturé ou scellé |
| 400 | ValueError | Quantité ≤ 0 |

## Exemple local (curl)

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

Résultat :
```json
{
  "id": "vente-xyz789",
  "service_id": "svc-abc123",
  "produit_id": "33export",
  "quantite": 2,
  "prix_unitaire": 650,
  "montant_total": 1300,
  "forme_paiement": "especes"
}
```

## Chemins de test

- `test_vente_domain.py::test_enregistrer_une_vente_emet_l_evenement` — Domaine pur
- `test_enregistrer_vente_handler.py::test_la_vente_est_persistee_journalisee_purgee_et_commitee` — Application + handler
- `test_enregistrer_vente_api.py::test_enregistrer_une_vente_cree_la_vente_et_journalise` — API intégration

---

**Statut** : ✅ LIVRÉ  
**PR** : Mergée sur `main`  
**Dernier commit** : feat(service_ventes): enregistrer une vente
