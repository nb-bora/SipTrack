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

### 📋 Prévues

| # | Fonctionnalité | Dépendances |
|---|---|---|
| 5 | Régler une addition | Dépend de #4 (Ouvrir une addition) |
| 6 | Paiement partiel | Dépend de #5 (Régler une addition) |
| 7 | Crédit client | Dépend de #6 (Paiement partiel) |
| 8 | Sous-caisse serveuse | Dépend de #2 (Enregistrer une vente) |

## 📊 Métriques

| Métrique | Valeur |
|---|---|
| **Tests (total)** | 46 |
| **Couverture domaine** | 100% |
| **Temps CI/CD** | ~1.5 min |
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
│   │   └── ouvrir_addition.py
│   ├── dto.py           ← Commandes et DTOs
│   └── ports/           ← Interfaces (Repository, Journal, Clock)
│
├── infrastructure/      ← ORM Django, repos concrets
│   ├── django_app/
│   │   └── models.py    ← ServiceModel, VenteModel, etc.
│   ├── persistence/
│   │   ├── repository.py    ← DjangoServiceRepository, etc.
│   │   └── mapper.py        ← Traduction domaine ↔ ORM
│   └── journal.py       ← Enregistrement des événements
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
uv run pytest                        # Tous les tests (46)
uv run pytest tests/unit/            # Domaine uniquement
uv run pytest tests/integration/     # API + E2E
```

## 🎯 Patterns appliqués

### Petits agrégats (ADR-0004)

Chaque agrégat a une seule responsabilité :
- `Service` → Cycle de vie du service, caisse
- `Vente` → Une transaction produit
- `Addition` → Groupage de ventes par table

→ Pas de FK ORM inter-agrégats ; référence par identité (string)

### Événements domaine

Chaque cas d'usage produit un événement horodaté :
- `ServiceOuvert` → Déclenche journalisation
- `VenteEnregistree` → Alimente le flux de trésorerie
- `ServiceCloture` → Marque clôture de service
- `AdditionOuverte` → Crée une addition

### Cohérence eventual (ADR-0004)

Les invariants inter-agrégats sont gardées au use case suivant :
- Exemple : « Ne clôturer un service que si aucune Addition n'est ouverte »
  - V1 (actuelle) : juste la transition d'état (OUVERT → CLÔTURÉ)
  - V2 (quand Addition arrive) : ajout du garde-fou dans `CloturerServiceHandler`

## 📚 Références

- **Modèle métier complet** : [docs/02-modele-metier.md](../../02-modele-metier.md)
- **Architecture backend** : [docs/03-architecture-backend.md](../../03-architecture-backend.md)
- **ADRs & décisions** : [docs/decisions/SYNTHESE-ADR.md](../../decisions/SYNTHESE-ADR.md)
- **Guide de contribution** : [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**Dernière mise à jour** : 2026-07-28  
**Auteur** : Claude Code (Community)
