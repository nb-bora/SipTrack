# Fonctionnalité : Crédit client

## Vue d'ensemble

**Domaine** : Crédit & Créances (nouveau bounded context)
**Acteurs** : Serveuse (elle accorde) · Gérante (elle suit et encaisse)
**Déclencheur** : Une table part sans payer
**Résultat** : L'addition est réglée, et une **dette existe au nom de quelqu'un**

## Le trou que ça ferme

Depuis la tranche 8, `forme_paiement = "credit"` était accepté. L'addition passait à
`reglee`, aucun argent n'entrait, et **personne ne devait rien**. La consommation
s'évaporait du décompte — exactement le trou que la tranche 8 avait fermé pour les
autres formes de paiement, rouvert par celle-là.

```
AVANT                                  APRÈS
addition 5 000 payée « credit »        addition 5 000 payée « credit »
→ addition reglee                      → addition reglee
→ 0 F encaissé                         → 0 F encaissé
→ personne ne doit rien   ❌           → Jean doit 5 000  ✓
```

## Flux principal

```
La table 5 part sans payer
    → POST .../paiements/  { montant: 5000, forme_paiement: "credit",
                             client_id: "cli-123" }
    → l'addition se règle : la table est libérée
    → une créance naît au nom de Jean, dans la MÊME transaction
    ✓ PaiementRecu + CreditAccorde partent ensemble au journal

Jean revient et rembourse 2 000
    → POST /api/credits/{id}/remboursements/  { montant: 2000 }
    → reste 3 000, la dette vit toujours

Jean solde
    → reste 0 → CreditSolde, automatiquement
```

## Contrats API

### Enregistrer un client — `POST /api/clients/`

| Champ | Type | Description |
|---|---|---|
| `bar_id` | str | Le bar |
| `nom` | str | Le nom sous lequel la dette est tenue |

**Idempotent** : un nom déjà connu dans ce bar renvoie le client existant. Refuser
créerait deux dettes séparées pour une même personne — précisément ce qu'on veut éviter.

### Payer en crédit — `POST /api/services/{sid}/additions/{aid}/paiements/`

Le champ `client_id` s'ajoute aux paiements existants. **Obligatoire si — et seulement
si — `forme_paiement` vaut `credit`.**

### Encaisser un remboursement — `POST /api/credits/{credit_id}/remboursements/`

```json
{ "montant": 2000 }
```
```json
{ "id": "cre-1", "montant": 5000, "rembourse": 2000, "reste": 3000, "statut": "ne" }
```

### Les encours — `GET /api/clients/{id}/encours/` · `GET /api/bars/{id}/encours/`

La vue de la gérante : qui doit quoi. Un client dont toutes les dettes sont éteintes
ne figure pas dans la liste du bar.

## Décisions de conception

### Un crédit règle l'addition

La table est rendue, la consommation est comptée. C'est la **créance** — pas
l'addition — qui reste ouverte. L'alternative aurait été de laisser l'addition
ouverte : le garde-fou de clôture (tranche 9) aurait alors bloqué la fermeture du
service toute la nuit à cause d'un seul client à crédit.

### Le crédit n'entre pas dans l'attendu de la sous-caisse

Aucun argent n'est remis de la main à la main : l'exiger de la serveuse créerait un
faux manquant. La réconciliation de la tranche 12 ne compte que les espèces, et
continue de le faire sans modification.

### Un crédit sans client est refusé

Un crédit sans débiteur est exactement le trou qu'on ferme. Le refus vient du **cas
d'usage**, pas du sérialiseur : c'est une règle métier, pas une contrainte de format.

### Ce qui a été remboursé n'est pas stocké

Chaque remboursement est une ligne ; le reste dû se **recalcule** à la lecture, comme
le total d'une addition se recalcule depuis ses ventes. Un solde stocké est un solde
qui finit par mentir — et chaque remboursement garde ainsi son auteur et son heure.

### Une addition n'engendre qu'une seule créance

Deux créances pour une même consommation feraient payer le client deux fois. Garanti
aussi par une contrainte d'unicité en base, qui tient même si deux requêtes
concurrentes passent la vérification applicative.

### Le nom suffit

Ni téléphone ni pièce d'identité. En exiger ferait renoncer la serveuse au mauvais
moment — et un crédit non saisi est bien pire qu'un crédit peu renseigné.

## Comment les deux contextes se parlent

Service & Ventes et Crédit & Créances **ne se connaissent pas** (ADR-0005).

```
service_ventes.application.ports.OuvertureDeCreance   ← le port, en son vocabulaire
                     ▲
                     │ implémenté par
                     │
config/creances.py::CreanceViaContexteCredit          ← composition root, seul
                     │                                   endroit voyant les deux
                     ▼
credit_creances.application.use_cases.accorder_credit
```

Service & Ventes déclare : « une consommation servie sans argent doit laisser une
dette quelque part ». Il ignore ce qu'est un crédit et comment il se rembourse.
L'adaptateur traduit même les exceptions (`ClientIntrouvable` → `ClientInconnu`)
pour qu'aucun vocabulaire étranger ne franchisse la frontière.

Le tout dans **une seule transaction** : il ne peut pas exister de crédit encaissé
sans créance en face. Si le client est inconnu, le paiement lui-même est annulé.

> Le jour où un bus d'événements existera, `config/creances.py` disparaîtra,
> remplacé par un abonnement à `PaiementRecu`. Le reste ne bougera pas.

## Événements produits

```
CreditAccorde            RemboursementRecu         CreditSolde
├─ credit_id             ├─ remboursement_id       ├─ credit_id
├─ client_id             ├─ credit_id              ├─ client_id
├─ service_id            ├─ client_id              └─ auteur_id
├─ addition_id           ├─ montant
├─ montant               └─ auteur_id
└─ auteur_id
```

## Erreurs possibles

| Code | Exception | Raison |
|---|---|---|
| 400 | ValidationError | Montant ≤ 0 |
| 404 | CreditIntrouvable | Le crédit n'existe pas |
| 409 | ClientRequisPourUnCredit | Crédit sans débiteur désigné |
| 409 | ClientInconnu | Le client désigné n'existe pas |
| 409 | CreditDejaSolde | La dette est déjà éteinte |
| 409 | RemboursementSuperieurAuReste | Rendre la monnaie est un autre Fait |
| 409 | CreditDejaOuvertPourCetteAddition | Ferait payer deux fois |

## Chemins de test

- `test_credit_domain.py` — naissance, extinction, remboursement comme Fait
- `test_credit_handlers.py` — client idempotent, double créance, sur-remboursement
- `test_credit_api.py` — bout en bout, dont « un crédit sans client est refusé » et
  « le crédit n'entre pas dans l'attendu de la sous-caisse »

## Composition verticale

| Couche | Fichiers |
|---|---|
| **Domaine** | `client.py` · `credit.py` · `remboursement.py` · `events.py` |
| **Application** | `creer_client.py` · `accorder_credit.py` · `enregistrer_remboursement.py` · `queries.py` |
| **Infrastructure** | `ClientModel`, `CreditModel`, `RemboursementModel` (migration `0001`) |
| **Interface** | `views.py` — clients, remboursements, encours |
| **Liaison** | `service_ventes/application/ports.py` · `config/creances.py` |

## Hors périmètre

- **Politique de crédit et plafond** (invariant 10 : « encours ≤ plafond configurable ») :
  suppose un paramétrage par bar qui n'existe pas encore.
- **Passer une créance en perte** : « décision gérante, au cas par cas, jamais
  automatique ». C'est un cas d'usage à part entière, avec son propre Fait.
- **Relances et échéancier** : le modèle mentionne un crédit « rééchelonné » ; rien
  n'est encore modélisé pour cela.
- **Rattacher un client à un compte utilisateur** : un client n'est pas un employé.

---

**Statut** : ✅ LIVRÉ (branche `feat/credit-client`, ticket #11)
**Tests** : 26 ajoutés (4 domaine · 10 handler · 12 API)
**Quality Gate** : Ruff ✓ + MyPy ✓ + lint-imports 5/5 ✓ + 174 tests ✓
**Dernière mise à jour** : 2026-07-28
