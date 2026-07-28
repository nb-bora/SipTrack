# Fonctionnalité : Sous-caisse serveuse (réconciliation quotidienne)

## Vue d'ensemble

**Domaine** : Service & Ventes
**Acteurs** : Serveuse (elle verse) · Gérante (elle contrôle)
**Déclencheur** : Fin de service — chaque serveuse remet sa recette
**Résultat** : Ce qu'elle a encaissé est confronté à ce qu'elle remet ; tout écart devient un Fait

C'est la première des **deux réconciliations emboîtées** du modèle métier (§9) : *par serveuse,
sur l'argent*. Le contrôle quotidien de l'outil.

## Ce que ça attrape — et ce que ça n'attrape pas

| | |
|---|---|
| ✅ **Attrapé** | « A saisi une vente et gardé le cash » — contrôle **quotidien**, sur l'argent |
| ❌ **Non attrapé** | « A vendu sans saisir » (vente au noir) — invisible ici, seul un **inventaire physique** la révèle |

> Corollaire à communiquer, et à ne jamais laisser sous silence : une clôture « caisse OK »
> **ne signifie pas** « aucun vol ». La vérité du stock vient des inventaires.

## Flux principal

```
Fin de service, la serveuse remet 1 800
    → POST /api/services/{sid}/versement/
    → attendu = Σ de SES encaissements en espèces sur CE service
    → écart = versé − attendu = −200
    → RecetteVersee + EcartConstate partent ensemble au journal
    ✓ le manquant est écrit, pas absorbé

La gérante contrôle
    → GET /api/services/{sid}/sous-caisses/
    ✓ par personne : encaissé espèces, encaissé mobile money, versé, écart
```

## Contrats API

### Verser sa recette — `POST /api/services/{service_id}/versement/`

| Champ | Type | Description |
|---|---|---|
| `montant` | int | XAF remis, ≥ 0 |

L'identité de la serveuse **vient du jeton**. Elle verse pour elle-même ; personne ne verse au
nom d'une autre.

```json
{
  "id": "vrs-123",
  "service_id": "svc-123",
  "serveuse_id": "7",
  "attendu": 2000,
  "verse": 1800,
  "ecart": -200
}
```

### Vue de la gérante — `GET /api/services/{service_id}/sous-caisses/`

```json
[
  { "serveuse_id": "7", "encaisse_especes": 2000, "encaisse_mobile_money": 5000,
    "verse": 1800, "ecart": -200 },
  { "serveuse_id": "9", "encaisse_especes": 1300, "encaisse_mobile_money": 0,
    "verse": null, "ecart": null }
]
```

`verse` et `ecart` valent `null` tant que la personne n'a pas versé — **et non zéro** : « n'a pas
encore versé » et « a versé zéro » sont deux situations différentes.

## Décisions de conception

### Le mobile money n'entre pas dans l'attendu

Il n'est pas remis de la main à la main. L'exiger dans la recette créerait un **faux manquant**
systématique. Il est affiché à part, pour information : la gérante voit l'activité complète.

### Les serveuses sont déduites des encaissements

Le contexte ne connaît pas encore l'affectation du personnel. Toute personne ayant encaissé
apparaît dans la vue — **y compris la gérante**, conformément au principe « personne n'échappe
au journal ».

### Un écart d'un franc est un écart

Aucun seuil de tolérance (invariant 4, « zéro inexpliqué »). Un excédent est signalé au même
titre qu'un manquant : les deux sont **inexpliqués**. Une caissière honnête est protégée par la
trace, pas par l'indulgence.

### Un seul versement par serveuse et par service

Un second masquerait le premier. Une correction s'écrit par **contre-passation**, pas en
repassant par-dessus. Garanti aussi par une contrainte d'unicité en base.

## Événements produits

```
RecetteVersee                    EcartConstate (si écart ≠ 0)
├─ versement_id: str             ├─ versement_id: str
├─ service_id: str               ├─ service_id: str
├─ serveuse_id: str              ├─ serveuse_id: str
├─ attendu: int (XAF)            ├─ ecart: int (signé)
├─ verse: int (XAF)              └─ auteur_id: str
└─ auteur_id: str
```

Les deux partent **ensemble** dans la même transaction : un versement qui ne tombe pas juste ne
peut pas être journalisé sans son écart.

## Erreurs possibles

| Code | Exception | Raison |
|---|---|---|
| 400 | ValidationError | Montant négatif |
| 404 | ServiceIntrouvable | Service n'existe pas |
| 409 | ServiceNonOuvert | Service clôturé ou scellé |
| 409 | RecetteDejaVersee | Cette serveuse a déjà versé sur ce service |

## Chemins de test

- `test_versement_domain.py` — écart nul, manquant, excédent, écart d'un franc
- `test_verser_recette_handler.py` — attendu calculé, double versement, service clôturé
- `test_sous_caisse_api.py` — bout en bout, dont « le mobile money n'entre pas dans l'attendu »

## Composition verticale

| Couche | Fichiers |
|---|---|
| **Domaine** | `domain/versement.py` · `events.py::RecetteVersee, EcartConstate` |
| **Application** | `use_cases/verser_recette.py` · `queries.py::SousCaisseQueryService` |
| **Infrastructure** | `VersementModel` + `auteur_id` sur `PaiementModel` (migration `0007`) |
| **Interface** | `views.py::VersementCreateView, SousCaisseListView` |

## Hors périmètre

- **Exiger que toutes les serveuses aient versé avant de clôturer le service** : suppose de
  connaître l'équipe affectée, ce que le contexte ne sait pas encore.
- **Résoudre un écart** (justification, contre-passation, mise à la charge de quelqu'un) : l'écart
  est constaté, son traitement reste à modéliser.
- **La réconciliation au niveau du service** (stock sorti vs Σ ventes + offerts + casse) : elle
  suppose le contexte Stock & Inventaire.

---

**Statut** : ✅ LIVRÉ (branche `feat/sous-caisse-serveuse`, ticket #12)
**Tests** : 20 ajoutés (5 domaine + 5 handler + 10 API)
**Quality Gate** : Ruff ✓ + MyPy ✓ + lint-imports ✓ + 148 tests ✓
**Dernière mise à jour** : 2026-07-28
