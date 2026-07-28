# 📖 Domaine : Service & Ventes

Gestion des services, ventes, additions et reglements de tables. Contexte central de SipTrack.

## Fonctionnalités

### ✅ Livrées

| # | Fonctionnalité | Statut | Doc |
|---|---|---|---|
| 1 | [Ouvrir un service](./01-ouvrir-un-service.md) | ✅ LIVRÉ | [Lire](./01-ouvrir-un-service.md) |
| 2 | [Enregistrer une vente](./02-enregistrer-une-vente.md) | ✅ LIVRÉ | [Lire](./02-enregistrer-une-vente.md) |
| 3 | [Clôturer un service](./03-cloturer-un-service.md) | ✅ LIVRÉ | [Lire](./03-cloturer-un-service.md) |
| 4 | [Ouvrir une addition](./04-ouvrir-une-addition.md) | ✅ LIVRÉ | [Lire](./04-ouvrir-une-addition.md) |
| 5 | [Régler une addition](./05-regler-une-addition.md) | ✅ LIVRÉ | [Lire](./05-regler-une-addition.md) |
| 6 | [Rattacher une vente à une addition](./06-rattacher-une-vente-a-une-addition.md) | ✅ LIVRÉ | [Lire](./06-rattacher-une-vente-a-une-addition.md) |
| 7 | Garde-fou de clôture (aucune addition ouverte) | ✅ LIVRÉ | [Lire](./03-cloturer-un-service.md) |
| 8 | [Encaisser un paiement (partiel ou total)](./07-encaisser-un-paiement.md) | ✅ LIVRÉ | [Lire](./07-encaisser-un-paiement.md) |
| 9 | [Sous-caisse serveuse (réconciliation)](./08-sous-caisse-serveuse.md) | ✅ LIVRÉ | [Lire](./08-sous-caisse-serveuse.md) |

### 📋 Prévues

| # | Fonctionnalité | Dépendances |
|---|---|---|

## 📊 Métriques

| Métrique | Valeur |
|---|---|
| **Tests (total)** | 174 |
| **Couverture domaine** | 100% |
| **Temps CI/CD** | ~2 min |
| **Linting** | ✓ Ruff |
| **Typage** | ✓ MyPy strict |
| **Architecture** | ✓ Import-linter |

## 🏗️ Architecture

Le domaine suit **DDD + Clean Architecture** (voir [docs/decisions/SYNTHESE-ADR.md](../../decisions/SYNTHESE-ADR.md)) :

```
Backend/contexts/service_ventes/
├── domain/              ← Logique métier pur (0 Django)
│   ├── service.py       ← Agrégat Service
│   ├── vente.py         ← Agrégat Vente
│   ├── addition.py      ← Agrégat Addition
│   ├── events.py        ← Événements domaine
│   └── exceptions.py    ← Exceptions métier
│
├── application/         ← Orchestration, ports
│   ├── use_cases/
│   │   ├── ouvrir_service.py
│   │   ├── enregistrer_vente.py
│   │   ├── cloturer_service.py
│   │   ├── ouvrir_addition.py
│   │   └── regler_addition.py
│   ├── dto.py           ← Commandes et DTOs (écriture)
│   └── queries.py       ← Port + DTO de lecture (CQRS)
│
├── infrastructure/      ← ORM Django, repos concrets
│   ├── django_app/
│   │   └── models.py    ← ServiceModel, VenteModel, etc.
│   ├── persistence/
│   │   ├── repository.py     ← DjangoServiceRepository, etc.
│   │   ├── query_service.py  ← Lecture (total d'addition)
│   │   └── mapper.py         ← Traduction domaine ↔ ORM
│   └── (le journal ne vit plus ici — voir shared/infrastructure/journal/)
│
└── interface/rest/      ← API DRF
    ├── views.py         ← Endpoints
    ├── serializers.py   ← Serializers
    └── urls.py          ← Routes
```

## 🧪 Tests

### Pyramide des tests

```
Intégration (API, endpoint-to-endpoint)
    ↑
Application (handler + fakes)
    ↑
Domaine (pur, 0 Django)  ← MAJORITÉ
```

### Par fonctionnalité

Chaque fonctionnalité livrée a **3 niveaux de tests** :

1. **Domaine** (`test_*_domain.py`) — Logique métier pur
2. **Handlers** (`test_*_handler.py`) — Orchestration + persistance
3. **API** (`test_*_api.py`) — Bout en bout via HTTP

Exemple pour « Ouvrir un service » :
```
test_service_domain.py
├── test_ouvrir_service_met_le_statut_a_ouvert
├── test_ouvrir_service_emet_l_evenement
└── test_ouvrir_un_service_ferme_ne_peut_etre_rouvert

test_ouvrir_service_handler.py
├── test_le_service_est_ajoute_et_le_dto_est_renvoye
├── test_la_persistance_est_appelee
├── test_l_evenement_est_journalise
└── ... (fakes en mémoire)

test_ouvrir_service_api.py
├── test_ouvrir_service_cree_le_service_et_journalise_le_mouvement
├── test_ouvrir_un_service_avec_montant_negatif_renvoi_400
└── test_retrier_ouvrir_service_est_idempotent
```

Lancer les tests :
```bash
cd Backend
uv run pytest                                    # Tous les tests (174)
uv run pytest -k domain                          # Domaine uniquement
uv run pytest -k api                             # API + E2E
```

## 🎯 Patterns appliqués

### Petits agrégats (ADR-0004)

Chaque agrégat a une seule responsabilité :
- `Service` → Cycle de vie du service, caisse
- `Vente` → Une transaction produit
- `Addition` → Groupage de ventes par table
- `Paiement` → Un encaissement porté à une addition
- `Versement` → La recette qu'une serveuse remet, et son écart

→ Pas de FK ORM inter-agrégats ; référence par identité (string)

### Événements domaine

Chaque cas d'usage produit un événement horodaté :
- `ServiceOuvert` → Déclenche journalisation
- `VenteEnregistree` → Alimente le flux de trésorerie
- `ServiceCloture` → Marque clôture de service
- `AdditionOuverte` → Crée une addition

### Cohérence eventual (ADR-0004)

Les invariants inter-agrégats sont gardés au use case, pas dans l'agrégat :
- « Une vente ne se rattache qu'à une addition du même service, encore ouverte »
  → vérifié par `EnregistrerVenteHandler`, pas par `Vente`
- « Ne clôturer un service que si aucune Addition n'est ouverte »
  → gardé par `CloturerServiceHandler`, qui compte les additions ouvertes avant d'émettre
  `ServiceCloture`

### Lecture séparée de l'écriture (CQRS)

Le total d'une addition est **calculé à la lecture**, jamais stocké : le journal des faits est
la seule vérité, tous les états s'en déduisent. Il est produit par un query service
(`application/queries.py` pour le port, `persistence/query_service.py` pour l'adaptateur), qui
lit les tables sans reconstruire d'agrégat — charger toutes les ventes dans `Addition`
contredirait les petits agrégats.

## 📚 Références

- **Modèle métier complet** : [docs/02-modele-metier.md](../../02-modele-metier.md)
- **Architecture backend** : [docs/03-architecture-backend.md](../../03-architecture-backend.md)
- **ADRs & décisions** : [docs/decisions/SYNTHESE-ADR.md](../../decisions/SYNTHESE-ADR.md)
- **Guide de contribution** : [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**Dernière mise à jour** : 2026-07-28  
**Auteur** : Claude Code (Community)
