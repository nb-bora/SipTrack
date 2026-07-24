# 03 — Architecture Backend (DDD + Clean Architecture sur Django)

Blueprint technique du backend Django (API-only, DRF), servant `Frontend/` et `Mobile/`.
Prérequis : le [modèle métier](./02-modele-metier.md). Le *pourquoi* de chaque choix est
dans les [ADR](./decisions/).

## 1. Le principe fondateur

> **Le domaine est du Python pur. Il n'importe jamais Django.** Django (ORM, DRF) ne vit que
> dans les couches externes. Les objets métier et les tables de base sont **deux choses
> distinctes**, reliées par un *mapper* dans le repository.

C'est l'approche recommandée par *Architecture Patterns with Python* (Cosmic Python, annexe
Django) : on garde le modèle de domaine séparé des modèles ORM, le repository traduit de l'un
vers l'autre. Voir [ADR-0002](./decisions/0002-domaine-independant-de-django.md).

## 2. Les quatre couches (règle de dépendance vers l'intérieur)

```
Interface (DRF : viewsets, serializers, permissions, endpoint de sync)
        │  dépend de ↓
Application (Use cases / Service Layer, ports, DTO, CQRS queries)
        │  dépend de ↓
Domaine (agrégats, VO, domain events, policies, INTERFACES de repository)  ← ne dépend de RIEN
        ▲
Infrastructure (ORM Django, repos concrets, journal, read models, ACL)
   implémente les ports — la flèche pointe vers l'intérieur
```

- **Domaine** : Python pur ; règles et invariants. Zéro Django, zéro autre contexte.
- **Application** : orchestre les cas d'usage (Service Layer), gère les transactions
  (Unit of Work), définit les **ports techniques**. Zéro règle métier.
- **Infrastructure** : ORM, repositories concrets, journal, projections, adaptateurs. Django ici.
- **Interface** : DRF (endpoints, DTO, auth, sync). Django ici.

## 3. Patterns tactiques retenus

| Pattern | Où | Rôle |
|---|---|---|
| **Aggregate** | Domaine | Frontière de cohérence transactionnelle. Petits agrégats. |
| **Value Object** | Domaine | `Montant`, `Quantite`, `PrixDate`… immuables. |
| **Domain Event** | Domaine | « c'est arrivé » — découple et alimente le journal. |
| **Repository** (interface) | Domaine | Une **par racine d'agrégat**. |
| **Repository** (impl + mapper) | Infra | Traduit domaine ↔ modèles ORM Django. |
| **Service Layer / Use Case** | Application | Orchestration d'un cas d'usage. |
| **Unit of Work** | Application (port) / Infra (impl) | Transaction atomique par use case. |
| **DTO** | Interface / Application | Jamais exposer un modèle ORM ni un agrégat. |
| **Query Service** | Application / Infra | Lecture (CQRS), lit les read models. |
| **Anti-Corruption Layer** | Application (port) / Infra (impl) | Isole le monde externe (distributeur…). |

## 4. Domaine : les règles de design d'agrégats (Vernon)

Les 4 règles d'*Effective Aggregate Design* sont appliquées :

1. **Modéliser les vrais invariants dans la frontière** — seule la cohérence *immédiate* est
   dans l'agrégat.
2. **Petits agrégats** — `Service`, `Addition`, `SousCaisseServeuse`, `Credit`, `Livraison`,
   `Inventaire` sont **séparés**.
3. **Référence par identité** — un agrégat ne référence un autre que par son **ID**.
4. **Cohérence eventual hors frontière** — via Domain Events.

Conséquences concrètes :

- La règle « on ne clôture pas un service tant qu'une addition est ouverte » n'est **pas** un
  invariant d'un seul agrégat : elle est vérifiée par un **use case** (qui interroge les
  additions ouvertes avant d'émettre `ServiceCloture`). Cohérence **coordonnée**.

## 5. Le journal & la persistance

- Le **journal d'audit immuable** (`Mouvement`, append-only, jamais `UPDATE`/`DELETE`) est une
  **exigence du domaine**, avec contre-passation obligatoire.
- **Comment** on le stocke (table append-only simple *ou* vrai event store) est un **détail
  d'infrastructure**, caché derrière un port `Journal`. On démarre **state-based** ; l'event
  sourcing reste possible sans toucher au domaine. Voir
  [ADR-0003](./decisions/0003-journal-audit-vs-event-sourcing.md).
- Métadonnées obligatoires d'un Mouvement : `auteur`, `capacite`, `service`, `bar`,
  **double horodatage** (saisie/réception), **séquence par appareil**, `idempotency_key`.

## 6. CQRS (indépendant de l'event sourcing)

- **Écriture** : `Command → use case → agrégat (invariants) → events → journal + persistance`.
- **Lecture** : des **query services** lisent des **read models** (`StockCourant`,
  `SoldeCaisse`, `EncoursCredits`, `BilanService`, `ConsolidationMultiBar`) — sans passer par
  les agrégats.

## 7. Isolation des bounded contexts

Voir [ADR-0005](./decisions/0005-isolation-bounded-contexts.md).

- **Aucune ForeignKey ORM entre contextes.** On référence par **identifiant**.
- Intégration via **Domain Events**, **Anti-Corruption Layer**, **Published Language**.
- Exemple : le `PrixDate` est **copié** dans la vente au moment où elle survient (jamais lu en
  direct depuis Catalogue) → l'historique reste vrai.

## 8. Composition Root

Un **unique point de câblage** (`config/container.py`, invoqué au démarrage Django) branche
les adaptateurs d'infrastructure sur les ports du domaine/application. C'est ce qui réalise
concrètement l'inversion de dépendances.

## 9. Ingestion offline (mobile)

Un **endpoint de sync** reçoit des **lots d'événements** produits sur le téléphone, valide les
métadonnées (séquence appareil, double horodatage, `idempotency_key`), **append** au journal,
rejoue les read models. Append-only + idempotence ⇒ **pas de conflit d'écrasement**. Un
service **scellé** rejette (ou reroute) les événements tardifs.

## 10. Arborescence cible

```
Backend/
├── config/
│   ├── settings/{base,dev,prod}.py
│   ├── urls.py
│   ├── container.py          # COMPOSITION ROOT
│   └── asgi.py
├── shared/                    # types génériques (PAS un Shared Kernel DDD)
│   ├── domain/                # Money, Quantite, Ids, Attribution, DomainEvent (base)
│   └── application/           # ports transverses : Clock, UnitOfWork, EventBus
└── contexts/
    └── service_ventes/            # patron répété par contexte
        ├── domain/                # PYTHON PUR
        │   ├── model/             # agrégats, entités, VO
        │   ├── events/            # domain events
        │   ├── services/          # domain services (Reconciliation)
        │   ├── policies/          # Tolerance, Delegation (specifications)
        │   └── repositories.py    # INTERFACES de repository
        ├── application/
        │   ├── use_cases/         # command handlers
        │   ├── queries/           # query services (read side)
        │   ├── ports/             # ports techniques + interfaces ACL
        │   └── dto/
        ├── infrastructure/
        │   ├── django_app/        # models.py, migrations/, apps.py (détail interne)
        │   ├── persistence/       # repos concrets + mappers
        │   ├── acl/               # implémentations Anti-Corruption
        │   ├── journal/           # impl du port Journal (append-only)
        │   └── read_models/       # impl des query services
        └── interface/
            └── rest/              # DRF : viewsets, serializers (DTO), urls, permissions
```
Mêmes 4 couches pour `stock_inventaire`, `credit_creances`, `approvisionnement`, `catalogue`,
`gouvernance_acces`. Chaque `infrastructure/django_app` est ajouté à `INSTALLED_APPS`.

## 11. Flux d'un cas d'usage (« Enregistrer une vente »)

1. **Interface (DRF)** : reçoit le JSON, authentifie, mappe en **Command** (DTO). Aucune règle.
2. **Application** : ouvre une `UnitOfWork`, charge **un** agrégat via son Repository, consulte
   les ports (Gouvernance/ACL) si besoin.
3. **Domaine** : l'agrégat applique ses invariants et **produit des Domain Events**.
4. **Application** : persiste l'agrégat, **append** au `Journal`, publie les events (les autres
   agrégats/read models réagissent en *eventual consistency*), commit.
5. **Interface** : renvoie un **DTO**.

## 12. Discipline (règles vérifiées, pas des vœux)

- **`import-linter`** en CI : `contexts.*.domain` ne peut importer ni `django` ni un autre
  contexte ; le sens des dépendances est respecté.
- **Tests en pyramide** : domaine **sans Django** (rapide) ; use cases avec repositories
  **in-memory** ; infra/API en intégration.

## 13. Pièges Django-DDD à éviter

- ❌ Logique métier dans `models.py` (ce sont des tables, pas des agrégats).
- ❌ `ModelSerializer` DRF exposant l'ORM (re-soude tout) → DTO explicites.
- ❌ Signaux Django pour la logique métier → Domain Events explicites.
- ❌ Sur-découpage : pour un outil interne de 2-3 bars, **rester pragmatique**.

## 14. Références

- Eric Evans — *Domain-Driven Design* (2003).
- Vaughn Vernon — *Implementing DDD* (2013) & *Effective Aggregate Design*.
- Robert C. Martin — *Clean Architecture* (2017).
- Percival & Gregory — *Architecture Patterns with Python* (Cosmic Python),
  https://www.cosmicpython.com — Repository / Unit of Work / Service Layer + annexe Django.
- ADR : https://adr.github.io — format Nygard / MADR.
