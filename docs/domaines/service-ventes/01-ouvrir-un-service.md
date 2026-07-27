# Fonctionnalité : Ouvrir un service

## Vue d'ensemble

**Domaine** : Service & Ventes  
**Acteur** : Gérante  
**Déclencheur** : Démarrage de l'activité du jour  
**Résultat** : Un nouveau service est créé et prêt à recevoir des ventes

## Flux principal

```
Gérante veut ouvrir un service
    → POST /api/services/
    → Crée agrégat Service (statut=OUVERT)
    → Enregistre événement ServiceOuvert
    → Retourne ServiceDTO avec id + statut + horodatage
    ✓ Service prêt à accueillir des ventes
```

## Contrats API

### Entrée (OuvrirServiceCommand)

| Champ | Type | Description |
|---|---|---|
| `bar_id` | str | Identifiant du bar |
| `auteur_id` | str | Identifiant de la gérante |
| `capacite` | str | Rôle (ex. "operatrice") |
| `fond_de_caisse` | int | Capital de démarrage (XAF) |

### Sortie (ServiceDTO)

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

## Invariants

- Montant `fond_de_caisse` ≥ 0
- Attribution unique : une seule gérante par service
- Un service démarre toujours au statut `OUVERT`

## Événement domaine produit

```
ServiceOuvert
├─ service_id: str
├─ bar_id: str
├─ auteur_id: str
└─ fond_de_caisse: int (montant en XAF)
```

## Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 400 | ValueError | Montant < 0 |
| 500 | SystemError | Impossible de générer un ID unique |

## Exemple local (curl)

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

Résultat :
```json
{
  "id": "svc-abc123",
  "bar_id": "bar1",
  "statut": "ouvert",
  "fond_de_caisse": 10000,
  "ouvert_le": "2026-07-28T10:00:00Z",
  "clos_le": null
}
```

## Chemins de test

- `test_service_domain.py::test_ouvrir_service_met_le_statut_a_ouvert` — Domaine pur
- `test_ouvrir_service_handler.py` — Application + handler
- `test_ouvrir_service_api.py::test_ouvrir_service_cree_le_service_et_journalise_le_mouvement` — API intégration

---

**Statut** : ✅ LIVRÉ  
**PR** : Mergée sur `main`  
**Dernier commit** : feat(service_ventes): ouvrir un service
