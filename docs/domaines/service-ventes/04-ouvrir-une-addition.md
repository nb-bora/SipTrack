# Fonctionnalité : Ouvrir une addition

## Vue d'ensemble

**Domaine** : Service & Ventes  
**Acteur** : Serveuse  
**Déclencheur** : Arrivée d'une nouvelle table  
**Résultat** : Une nouvelle addition est créée pour la table

## Flux principal

```
Serveuse ouvre une addition pour la table 5
    → POST /api/services/{service_id}/additions/
    → Charge Service (vérifier statut=OUVERT)
    → Crée agrégat Addition (statut=OUVERTE)
    → Enregistre événement AdditionOuverte
    → Retourne AdditionDTO
    ✓ Addition prête à recevoir des ventes
```

## Contrats API

### Entrée (OuvrirAdditionCommand)

| Champ | Type | Description |
|---|---|---|
| `service_id` | str | ID du service actif |
| `auteur_id` | str | ID de la serveuse |
| `table_numero` | int | Numéro de la table (≥ 1) |

### Sortie (AdditionDTO)

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

## Invariants

1. **Service ouvert** : `service.statut == OUVERT`
   - Lève : `ServiceNonOuvert`

2. **Table valide** : `table_numero ≥ 1`
   - Validé dans le serializer

3. **Statut initial** : toujours `OUVERTE`

## Événement domaine produit

```
AdditionOuverte
├─ addition_id: str
├─ service_id: str
├─ table_numero: int
└─ auteur_id: str
```

## Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | ServiceIntrouvable | Service n'existe pas |
| 409 | ServiceNonOuvert | Service clôturé ou scellé |
| 400 | ValidationError | table_numero < 1 |

## Exemple local (curl)

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

Résultat :
```json
{
  "id": "add-def456",
  "service_id": "svc-abc123",
  "table_numero": 5,
  "statut": "ouverte",
  "ouvert_le": "2026-07-28T10:15:00Z",
  "ferme_le": null
}
```

## Chemins de test

- `test_addition_domain.py::test_ouvrir_addition_met_le_statut_a_ouverte` — Domaine pur
- `test_ouvrir_addition_handler.py::test_l_addition_est_ajoutee_et_le_dto_est_renvoye` — Application + handler
- `test_ouvrir_addition_api.py::test_ouvrir_addition_cree_l_addition_et_journalise` — API intégration

---

**Statut** : ✅ LIVRÉ  
**PR** : #7 (en cours de review/merge)  
**Dernier commit** : feat(service_ventes): ouvrir une addition
