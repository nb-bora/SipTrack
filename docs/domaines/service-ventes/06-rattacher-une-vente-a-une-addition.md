# Fonctionnalité : Rattacher une vente à une addition

## Vue d'ensemble

**Domaine** : Service & Ventes  
**Acteur** : Serveuse  
**Déclencheur** : Une table consomme ; on veut savoir ce qu'elle doit  
**Résultat** : La consommation est rattachée à l'addition de la table, dont le total devient lisible

Jusqu'ici une vente n'était reliée à aucune table : « régler une addition » changeait un statut
sans qu'aucun montant ne soit réglé. Cette tranche relie les deux et ouvre le côté **lecture**
du contexte.

## Flux principal

```
Serveuse sert la table 5
    → POST /api/services/{service_id}/ventes/  avec addition_id
    → Charge Service (vérifier statut=OUVERT)
    → Charge Addition (même service ? encore ouverte ?)
    → Crée agrégat Vente porteur de addition_id
    → Enregistre événement VenteEnregistree (addition_id inclus)
    ✓ La consommation pèse sur l'addition de la table

Le client demande l'addition
    → GET /api/services/{service_id}/additions/{addition_id}/
    → Query service : lit les lignes, agrège le total
    ✓ Addition présentable, ligne par ligne
```

## Contrats API

### Rattacher une vente (`POST /api/services/{service_id}/ventes/`)

| Champ | Type | Description |
|---|---|---|
| `auteur_id` | str | ID de la serveuse |
| `produit_id` | str | ID du produit |
| `quantite` | int | Nombre d'unités (≥ 1) |
| `prix_unitaire` | int | Prix en XAF |
| `forme_paiement` | str | `especes` · `mobile_money` · `credit` |
| `addition_id` | str \| null | **Optionnel** — absent pour une vente au comptoir |

### Lire une addition (`GET /api/services/{service_id}/additions/{addition_id}/`)

```json
{
  "id": "add-789ghi",
  "service_id": "svc-123abc",
  "table_numero": 5,
  "statut": "ouverte",
  "ouvert_le": "2026-07-28T10:15:00Z",
  "ferme_le": null,
  "lignes": [
    {
      "vente_id": "vente-456def",
      "produit_id": "33export",
      "quantite": 2,
      "prix_unitaire": 650,
      "montant_total": 1300,
      "forme_paiement": "especes",
      "horodatage": "2026-07-28T20:10:00Z"
    }
  ],
  "total": 1300
}
```

## Invariants

1. **L'addition doit appartenir au service** de l'URL
   - Sinon `AdditionIntrouvable` (404) — on ne révèle pas l'existence d'une addition d'un autre service

2. **L'addition doit être ouverte** : `statut == OUVERTE`
   - Une addition réglée ou abandonnée a déjà été présentée au client ; y ajouter une
     consommation reviendrait à la modifier après coup
   - Lève `AdditionDejaCloturee` (409)

3. **Le rattachement est facultatif** : `addition_id` absent = vente au comptoir
   - Le modèle métier prévoit un **encaissement mixte** (caisse + salle)

4. **Le total est calculé, jamais stocké**
   - Il se déduit des lignes à chaque lecture, y compris après règlement

## Décision de conception : où vit le total ?

Le total **n'est pas porté par l'agrégat `Addition`**, et ce n'est pas un oubli :

- le calculer dans l'agrégat obligerait à charger toutes ses ventes, ce qui contredit
  [ADR-0004](../../decisions/0004-petits-agregats-coherence-eventual.md) (petits agrégats,
  référence par identité) ;
- le **stocker** créerait un état capable de diverger de ses faits, alors que le principe
  fondateur du produit est que le journal est la seule vérité et que **tous les états sont
  calculés**.

Il est donc produit côté lecture par un **query service** (CQRS), qui lit les tables sans
reconstruire d'agrégat. C'est la première brique de lecture du projet.

## Événement domaine produit

```
VenteEnregistree
├─ vente_id: str
├─ service_id: str
├─ addition_id: str | None   ← nouveau
├─ produit_id: str
├─ quantite: int
├─ prix_unitaire: int (XAF)
├─ montant_total: int (XAF, calculé)
├─ forme_paiement: str
└─ auteur_id: str
```

Le rattachement est visible **dans le journal**, pas seulement en base : un audit doit pouvoir
reconstituer à quelle table une consommation a été servie.

## Erreurs possibles

| Code HTTP | Exception | Raison |
|---|---|---|
| 404 | ServiceIntrouvable | Service n'existe pas |
| 404 | AdditionIntrouvable | Addition inexistante, ou rattachée à un autre service |
| 409 | ServiceNonOuvert | Service clôturé ou scellé |
| 409 | AdditionDejaCloturee | Addition déjà réglée ou abandonnée |

## Exemple local (curl)

```bash
SERVICE_ID=$(curl -s -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -d '{"bar_id":"bar1","auteur_id":"u1","capacite":"operatrice","fond_de_caisse":10000}' \
  | jq -r '.id')

ADDITION_ID=$(curl -s -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/additions/ \
  -H "Content-Type: application/json" \
  -d '{"auteur_id":"u1","table_numero":5}' \
  | jq -r '.id')

# Deux consommations sur la table 5
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/ventes/ \
  -H "Content-Type: application/json" \
  -d "{\"auteur_id\":\"u1\",\"produit_id\":\"33export\",\"quantite\":2,\"prix_unitaire\":650,\"forme_paiement\":\"especes\",\"addition_id\":\"$ADDITION_ID\"}"

# Une vente au comptoir : elle ne pèse pas sur l'addition
curl -X POST http://127.0.0.1:8000/api/services/$SERVICE_ID/ventes/ \
  -H "Content-Type: application/json" \
  -d '{"auteur_id":"u1","produit_id":"33export","quantite":4,"prix_unitaire":650,"forme_paiement":"especes"}'

# L'addition de la table 5
curl http://127.0.0.1:8000/api/services/$SERVICE_ID/additions/$ADDITION_ID/
```

## Chemins de test

- `test_vente_domain.py` — la vente porte (ou non) une addition, événement inclus
- `test_addition_domain.py` — `accepter_consommation()` selon le statut
- `test_enregistrer_vente_handler.py` — rattachement, autre service, addition close
- `test_addition_lignes_api.py` — bout en bout : total, comptoir exclu, 404/409

## Composition verticale

| Couche | Fichiers |
|---|---|
| **Domaine** | `domain/vente.py::Vente.addition_id` · `domain/addition.py::accepter_consommation()` |
| **Application** | `application/use_cases/enregistrer_vente.py` · `application/queries.py` (port + DTO de lecture) |
| **Infrastructure** | `persistence/query_service.py::DjangoAdditionQueryService` · migration `0004` |
| **Interface** | `interface/rest/views.py::AdditionDetailView` |

## Hors périmètre (tickets à venir)

- Garde-fou « ne pas clôturer un service tant que des additions sont ouvertes » (invariant 9)
- Invariant 10 (`encours ≤ plafond`), qui suppose la Politique de crédit
- Paiement partiel (#10) et sous-caisse serveuse (#12), que cette tranche débloque

---

**Statut** : ✅ LIVRÉ (branche `feat/vente-addition`, ticket #22)  
**Tests** : 19 ajoutés (4 domaine + 5 handler + 9 API + 1 régression)  
**Quality Gate** : Ruff ✓ + MyPy ✓ + lint-imports ✓ + 78 tests ✓  
**Dernière mise à jour** : 2026-07-28
