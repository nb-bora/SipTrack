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
| 409 | AdditionsEncoreOuvertes | Des tables n'ont pas réglé |

## Garde-fou métier ✅

**La clôture est refusée tant qu'une addition reste ouverte** (invariant 9 du modèle métier).
Clôturer malgré tout ferait disparaître du décompte de la journée des consommations servies
mais non réglées — précisément ce que le produit doit rendre impossible.

```json
{ "detail": "Impossible de clôturer : 2 addition(s) encore ouverte(s)." }
```

La réponse dit **combien** : une gérante doit savoir ce qui lui reste à faire, pas seulement
qu'on lui refuse quelque chose.

Une addition `REGLEE` ou `ABANDONNEE` ne bloque pas.

### Où vit cette règle

Dans `CloturerServiceHandler`, **pas** dans l'agrégat `Service` : c'est un invariant
**inter-agrégats**, et `Service` n'a pas à connaître les additions
([ADR-0004](../../decisions/0004-petits-agregats-coherence-eventual.md)). Le handler interroge
le port `AdditionRepository.compter_ouvertes()`.

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
