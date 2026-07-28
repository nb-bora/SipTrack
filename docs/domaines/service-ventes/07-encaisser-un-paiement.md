# Fonctionnalité : Encaisser un paiement (partiel ou total)

## Vue d'ensemble

**Domaine** : Service & Ventes
**Acteur** : Serveuse
**Déclencheur** : Le client paie, en une ou plusieurs fois
**Résultat** : Le paiement est journalisé ; l'addition se règle quand elle est soldée

## Le changement de fond

Jusqu'ici, « régler une addition » était une **déclaration** : on basculait un statut sans
qu'aucun argent ne soit constaté. Le règlement devient une **conséquence** — l'addition passe
à `reglee` quand le cumul des paiements couvre le total consommé, et pas avant.

## Flux principal

```
Le client paie 500 sur une addition de 2 000
    → POST /api/services/{sid}/additions/{aid}/paiements/
    → Charge l'addition (même service ? encore ouverte ?)
    → reste dû = Σ ventes − Σ paiements
    → Refuse si le montant dépasse le reste
    → Enregistre le Paiement, émet PaiementRecu
    ✓ reste_a_payer = 1 500, addition toujours ouverte

Le client solde les 1 500
    → même endpoint
    → le cumul couvre le total : l'addition se règle d'elle-même
    → PaiementRecu + AdditionReglee, dans la même transaction
    ✓ addition « reglee », la table peut partir
```

## Contrats API

### Encaisser — `POST /api/services/{service_id}/additions/{addition_id}/paiements/`

| Champ | Type | Description |
|---|---|---|
| `montant` | int | XAF, strictement positif |
| `forme_paiement` | str | `especes` · `mobile_money` · `credit` |

```json
{
  "id": "pmt-123",
  "addition_id": "add-789",
  "service_id": "svc-123",
  "montant": 500,
  "forme_paiement": "especes",
  "reste_a_payer": 1500
}
```

### Lire l'addition — `GET /api/services/{sid}/additions/{aid}/`

Expose désormais `paiements`, `paye` et `reste_a_payer`, **tous calculés** à la lecture :

```json
{
  "statut": "ouverte",
  "total": 2000,
  "paye": 500,
  "reste_a_payer": 1500,
  "paiements": [
    { "paiement_id": "pmt-123", "montant": 500, "forme_paiement": "especes",
      "horodatage": "2026-07-28T21:10:00Z" }
  ]
}
```

## Invariants

1. **Montant strictement positif** — un remboursement est un autre Fait, pas un paiement négatif
2. **Jamais plus que le reste dû** → `PaiementSuperieurAuReste` (409)
   Rendre la monnaie est un Fait distinct, hors périmètre de cette tranche
3. **L'addition doit être ouverte** → `AdditionDejaCloturee` (409)
4. **Le règlement suit le solde** : `paye == total` ⟹ `REGLEE`, automatiquement
5. **On ne clôt pas une addition non soldée** → `AdditionNonSoldee` (409)

## Le trou que ça ferme

`POST .../reglement/` permettait de clore une addition **sans avoir encaissé**. La créance
disparaissait alors du décompte, sans laisser de trace exploitable. Cet endpoint refuse
désormais toute addition dont le reste dû est positif ; il ne sert plus qu'à clore une table
qui n'a rien consommé.

## Événements produits

```
PaiementRecu                    AdditionReglee (si soldée)
├─ paiement_id: str             ├─ addition_id: str
├─ addition_id: str             ├─ service_id: str
├─ service_id: str              ├─ table_numero: int
├─ montant: int (XAF)           └─ auteur_id: str
├─ forme_paiement: str
└─ auteur_id: str
```

Les deux partent **ensemble** au journal, dans la même transaction : un encaissement qui
solde une table ne peut pas être enregistré sans son règlement, ni l'inverse.

## Erreurs possibles

| Code | Exception | Raison |
|---|---|---|
| 400 | ValidationError | Montant nul ou négatif, forme de paiement inconnue |
| 404 | AdditionIntrouvable | Addition inexistante, ou rattachée à un autre service |
| 409 | AdditionDejaCloturee | Addition déjà réglée ou abandonnée |
| 409 | PaiementSuperieurAuReste | Le montant dépasse ce que la table doit encore |
| 409 | AdditionNonSoldee | Tentative de clore une addition avec un reste dû |

## Exemple local (curl)

```bash
JETON=...   # cf. README

# ... service ouvert, addition ouverte, vente de 2 000 rattachée ...

curl -X POST http://127.0.0.1:8000/api/services/$SID/additions/$AID/paiements/ \
  -H "Authorization: Token $JETON" -H "Content-Type: application/json" \
  -d '{"montant": 500, "forme_paiement": "especes"}'
# {"reste_a_payer": 1500, ...}

curl -X POST http://127.0.0.1:8000/api/services/$SID/additions/$AID/paiements/ \
  -H "Authorization: Token $JETON" -H "Content-Type: application/json" \
  -d '{"montant": 1500, "forme_paiement": "mobile_money"}'
# {"reste_a_payer": 0, ...}  → l'addition est passée à « reglee »
```

## Chemins de test

- `test_paiement_domain.py` — invariants de l'agrégat, événement émis
- `test_enregistrer_paiement_handler.py` — partiel, solde, dépassement, addition close
- `test_paiement_api.py` — bout en bout, dont « clore sans encaisser est refusé »

## Composition verticale

| Couche | Fichiers |
|---|---|
| **Domaine** | `domain/paiement.py` · `domain/events.py::PaiementRecu` |
| **Application** | `use_cases/enregistrer_paiement.py` · `use_cases/regler_addition.py` |
| **Infrastructure** | `PaiementModel` (migration `0006`) · repository · query service |
| **Interface** | `views.py::PaiementCreateView` |

## Hors périmètre

- **Rendre la monnaie** : un Fait distinct, à modéliser (`PerteMonetaireConstatee` ou monnaie rendue)
- **Le crédit** (#11) : `forme_paiement = "credit"` est accepté comme forme, mais aucune créance
  client n'est encore créée — c'est l'objet du contexte Crédit & Créances
- **La sous-caisse serveuse** (#12) : la réconciliation « recette versée vs encaissements saisis »
  devient possible grâce à cette tranche

---

**Statut** : ✅ LIVRÉ (branche `feat/paiement-partiel`, ticket #10)
**Tests** : 20 ajoutés (4 domaine + 6 handler + 10 API)
**Quality Gate** : Ruff ✓ + MyPy ✓ + lint-imports ✓ + 128 tests ✓
**Dernière mise à jour** : 2026-07-28
