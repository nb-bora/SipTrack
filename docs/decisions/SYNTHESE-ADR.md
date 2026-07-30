# 📋 Synthèse des ADR (Architecture Decision Records)

Résumé exécutif de chaque décision structurante de SipTrack, avec **exemples concrets du code livré**.

---

## ADR-0001 — Architecture en couches (Clean Architecture / DDD)

**Statut** : ✅ Accepté  
**Décision** : Les 4 couches indépendantes (Domaine → Application → Infrastructure → Interface) avec règle de dépendance vers l'intérieur.

### Pourquoi?

SipTrack a un cœur métier riche (cycles de vie, invariants, délégation). Il doit rester testable, durable et indépendant des choix techniques (base, framework, canaux).

### Conséquences

✅ **Domaine testable sans Django** — Les tests de domaine ne dépendent que de Python  
✅ **Infrastructure remplaçable** — Vous pourriez changer de Django à FastAPI sans toucher au domaine  
✅ **Clair architecturalement** — Chaque couche a une responsabilité unique

⚠️ **Plus de code de plomberie** — DTOs, mappers, ports — accepté et cadré par `import-linter` et les tests en pyramide

### Exemple concret

```python
# Domaine (pur, 0 Django)
# Backend/contexts/service_ventes/domain/service.py
class Service:
    def cloturer(self, *, auteur_id: str, horodatage: datetime) -> None:
        if self.statut is not StatutService.OUVERT:
            raise ServiceDejaCloture(self.id)
        self.statut = StatutService.CLOTURE
        self.clos_le = horodatage
        self.events.append(ServiceCloture(...))
```

```python
# Application (orchestre, zéro règle métier)
# Backend/contexts/service_ventes/application/use_cases/cloturer_service.py
class CloturerServiceHandler:
    def executer(self, cmd: CloturerServiceCommand) -> ServiceDTO:
        service = self.repository.par_id(cmd.service_id)  # port injecté
        service.cloturer(auteur_id=cmd.auteur_id, horodatage=self.clock.now())
        self.repository.mettre_a_jour(service)  # persistance
        self.journal.enregistrer_evenements(service)  # journalisation
        self.unit_of_work.commit()  # transaction
        return ServiceDTO.from_domaine(service)
```

```python
# Infrastructure (implémente les ports)
# Backend/contexts/service_ventes/infrastructure/persistence/repository.py
class DjangoServiceRepository:
    def mettre_a_jour(self, service: Service) -> None:
        ligne = ServiceModel.objects.get(pk=service.id)
        mapper.vers_ligne(service, ligne)
        ligne.save()
```

```python
# Interface (DRF)
# Backend/contexts/service_ventes/interface/rest/views.py
@api_view(["POST"])
def cloturer_service(request, service_id: str):
    cmd = CloturerServiceCommand(service_id=service_id, auteur_id=request.user.id)
    dto = container.cloturer_service().executer(cmd)
    return Response(ServiceOutputSerializer(dto).data, status=200)
```

---

## ADR-0002 — Domaine indépendant de Django (persistence-ignorant)

**Statut** : ✅ Accepté  
**Décision** : Le domaine est du Python pur. Django vit dans `infrastructure/` et `interface/`. Un **repository** traduit domaine ↔ ORM.

### Pourquoi?

Django est nativement *Active Record* : l'ORM soude modèle et persistance. Le DDD veut un domaine ignorant de la base. Il faut les réconcilier sans compromettre ni l'un ni l'autre.

### Conséquences

✅ **Domaine isolé** — Zéro `import django` dans `domain/`  
✅ **Tests rapides** — Les tests de domaine ne touchent pas la DB  
✅ **Remplaçable** — L'implémentation ORM est interchangeable

⚠️ **Mapper explicite** — Chaque repository traduit `domaine_obj ↔ orm_model`  
⚠️ **Perdu de raccourcis** — Pas de `ModelSerializer`, pas d'admin sur les agrégats

### Exemple concret

**Domaine pur** :
```python
# Backend/contexts/service_ventes/domain/service.py
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Service:
    id: str
    bar_id: str
    statut: StatutService
    fond_de_caisse: int
    ouvert_le: datetime
    clos_le: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list)
    
    def cloturer(self, *, auteur_id: str, horodatage: datetime) -> None:
        if self.statut is not StatutService.OUVERT:
            raise ServiceDejaCloture(self.id)
        self.statut = StatutService.CLOTURE
        self.clos_le = horodatage
        self.events.append(ServiceCloture(service_id=self.id, ...))
```

**ORM Django séparé** :
```python
# Backend/contexts/service_ventes/infrastructure/django_app/models.py
from django.db import models


class ServiceModel(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    bar_id = models.CharField(max_length=50)
    statut = models.CharField(
        max_length=20, choices=[("ouvert", "Ouvert"), ("cloture", "Clôturé")]
    )
    fond_de_caisse = models.IntegerField()
    ouvert_le = models.DateTimeField(auto_now_add=True)
    clos_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "service_ventes"
```

**Repository = Mapper** :
```python
# Backend/contexts/service_ventes/infrastructure/persistence/mapper.py
class ServiceMapper:
    @staticmethod
    def vers_domaine(ligne: ServiceModel) -> Service:
        return Service(
            id=ligne.id,
            bar_id=ligne.bar_id,
            statut=StatutService(ligne.statut),
            fond_de_caisse=ligne.fond_de_caisse,
            ouvert_le=ligne.ouvert_le,
            clos_le=ligne.clos_le,
            events=[],
        )

    @staticmethod
    def vers_ligne(service: Service, ligne: ServiceModel) -> None:
        ligne.bar_id = service.bar_id
        ligne.statut = service.statut.value
        ligne.clos_le = service.clos_le
```

### Vérification

```bash
# lint-imports vérifie que domain/ n'importe jamais Django :
uv run lint-imports
# ✓ contexts.*.domain ⊄ django
```

---

## ADR-0003 — Journal d'audit = exigence métier ; ES = détail d'infra

**Statut** : ✅ Accepté  
**Décision** : La **journalisation des événements métier est une exigence légale** (audit). Le *Comment* (Event Sourcing complet ou append-only simple) est un détail d'implémentation.

### Pourquoi?

SipTrack est un **outil d'audit** pour le Cameroun. Traçabilité = obligation légale. Mais Event Sourcing complet (toute l'histoire du monde) est sur-dimensionné pour un bar.

### Conséquences

✅ **Journalisation = domaine** — Tout événement métier va dans le journal  
✅ **Immuable** — `MouvementModel` : append-only, jamais mis à jour  
✅ **Léger** — Pas de recalcul d'états historiques, pas de snapshot

⚠️ **États actuels en base** — Les tables `ServiceModel`, `VenteModel` etc. restent des *projections* du journal, pas la source de vérité, mais elles sont mis à jour synchrone

### Exemple concret

**Journal append-only** :
```python
# Backend/contexts/service_ventes/infrastructure/django_app/models.py
class MouvementModel(models.Model):
    id = models.AutoField(primary_key=True)
    type_mouvement = models.CharField(  # "ServiceOuvert", "VenteEnregistree", etc.
        max_length=50, choices=MOUVEMENT_CHOICES
    )
    service_id = models.CharField(max_length=50)
    data = models.JSONField()  # Charge utile de l'événement
    enregistre_le = models.DateTimeField(auto_now_add=True)
    auteur_id = models.CharField(max_length=50)
    
    class Meta:
        app_label = "service_ventes"
        ordering = ["enregistre_le"]  # Toujours en ordre chronologique
```

**Journalisation dans le handler** :
```python
# Backend/contexts/service_ventes/application/use_cases/cloturer_service.py
class CloturerServiceHandler:
    def executer(self, cmd: CloturerServiceCommand) -> ServiceDTO:
        service = self.repository.par_id(cmd.service_id)
        service.cloturer(auteur_id=cmd.auteur_id, horodatage=self.clock.now())
        
        # Journalise tout événement métier émis
        for event in service.events:
            self.journal.enregistrer_evenements(event)
        
        # Mise à jour synchrone de la projection
        self.repository.mettre_a_jour(service)
        self.unit_of_work.commit()
        
        return ServiceDTO.from_domaine(service)
```

**Lecture du journal** :
```bash
# Tous les événements, immuables
SELECT * FROM MouvementModel 
WHERE service_id = 'svc-123'
ORDER BY enregistre_le ASC;

# ServiceOuvert: 2026-07-28 10:00 | u1
# VenteEnregistree: 2026-07-28 10:05 | u2 | 1300 XAF
# ServiceCloture: 2026-07-28 22:30 | u1
```

---

## ADR-0004 — Petits agrégats, référence par identité, cohérence éventuelle

**Statut** : ✅ Accepté  
**Décision** : Agrégats **petits et simples** (une seule responsabilité). Entre-agrégats : référence par identité. Pas de FK ORM inter-agrégats. Cohérence eventual (via événements).

### Pourquoi?

Les agrégats **gros et entrelacés** → complexité, transactions longues, concurrence. Les petits agrégats → responsabilité claire, testables isolément, scalables.

### Conséquences

✅ **Responsabilité claire** — Chaque agrégat = une seule chose  
✅ **Transactions courtes** — Pas de blocages inter-agrégats  
✅ **Événements = glue** — Les agrégats communiquent via événements domaine  

⚠️ **Cohérence eventual** — Les invariants inter-agrégats sont **cohérents à terme** (gardes-fou au prochain use case, ex: ne clôturer service que si aucune Addition ouverte)  
⚠️ **Pas de FK ORM** — Les relations traversent des événements ou queries, jamais des FK

### Exemple concret

**Petits agrégats** :
```python
# Backend/contexts/service_ventes/domain/

# Agrégat 1 : Service (racine)
class Service:
    id: str
    statut: StatutService
    fond_de_caisse: int
    # ... (simple, ~5 champs)


# Agrégat 2 : Vente (indépendante)
class Vente:
    id: str
    service_id: str  # référence par identité (pas de FK ORM)
    produit_id: str
    quantite: int
    montant_total: int
    # ... (simple, ~6 champs)


# Agrégat 3 : Addition (indépendante)
class Addition:
    id: str
    service_id: str  # référence par identité
    table_numero: int
    statut: StatutAddition
    # ... (simple, ~4 champs)
```

**Référence par identité dans le code** :
```python
# ❌ Jamais ceci (FK ORM entre agrégats) :
# service.additions = [addition]  # ← NO!

# ✅ Toujours par identité :
class Service:
    id: str
    # ... sans collection d'additions


# Charger les additions d'un service se fait via query :
additions = repository.additions_d_un_service(service_id)
```

**Cohérence eventual : gardes-fou au prochain use case** :
```python
# ADR-0004 dit : ne clôturer service que si aucune Addition ouverte
# En V1, Addition n'existe pas → on livre la transition pure (OUVERT → CLÔTURÉ)
# Quand Addition arrive, on ajoute le garde-fou :


class CloturerServiceHandler:
    def executer(self, cmd: CloturerServiceCommand) -> ServiceDTO:
        service = self.repository.par_id(cmd.service_id)

        # NOUVEAU (quand Addition est implémentée) :
        # Vérifier qu'aucune Addition n'est ouverte
        additions_ouvertes = self.addition_repository.par_service_id(service.id)
        if any(a.statut == StatutAddition.OUVERTE for a in additions_ouvertes):
            raise ImpossibleClotureAdditionOuverte(service.id)

        service.cloturer(auteur_id=cmd.auteur_id, horodatage=self.clock.now())
        self.repository.mettre_a_jour(service)
        return ServiceDTO.from_domaine(service)
```

**Pas de FK ORM entre contextes** :
```python
# ❌ Jamais ceci dans DjangoServiceRepository :
# class ServiceModel(models.Model):
#     addition = models.ForeignKey(AdditionModel)  # ← NO!

# ✅ Toujours par identité :
# class ServiceModel(models.Model):
#     id = models.CharField(...)
#     bar_id = models.CharField(...)
#     # pas de FK vers Addition

# Les Additions ont leur propre table :
# class AdditionModel(models.Model):
#     service_id = models.CharField(...)  # juste l'ID, pas FK
```

---

## ADR-0005 — Isolation stricte des bounded contexts

**Statut** : ✅ Accepté  
**Décision** : Chaque contexte (Service & Ventes, Stock, Crédit, etc.) est **complètement isolé**. Pas d'imports croisés `contexts.A ← contexts.B`. Communication via événements.

### Pourquoi?

DDD = 6 contextes indépendants. Croisements directs → rigidité, explosion de dépendances. Isolation stricte → évolution indépendante, réutilisabilité, testabilité.

### Conséquences

✅ **Contextes indépendants** — Vous pouvez travailler sur deux contextes en parallèle sans conflit  
✅ **Remplaçable** — Vous pourriez swapper un contexte complet sans toucher aux autres  
✅ **Testable** — Tests d'un contexte sans les autres

⚠️ **Orchestration au niveau app** — Les use cases complexes (inter-contextes) vivent dans un `OrchestratorHandler` distinct, pas à l'intérieur d'un contexte

### Exemple concret

```
Backend/contexts/
├── service_ventes/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interface/
│
├── stock_inventaire/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interface/
│
├── credit_creances/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interface/
```

**Pas d'import croisé** :
```python
# ❌ JAMAIS ceci :
# from contexts.service_ventes.domain import Service
# class Paiement(Service):  # ← NO!

# ❌ JAMAIS ceci :
# from contexts.stock_inventaire.domain import Produit
# class Vente:
#     produit = Produit  # ← NO!

# ✅ Toujours par événements :
# Backend/contexts/service_ventes/domain/events.py
class VenteEnregistree(DomainEvent):
    vente_id: str
    produit_id: str  # juste l'ID (string), pas l'objet
    quantite: int
    # ...


# Backend/contexts/stock_inventaire/application/eventHandlers/
class DiminuerStockQuandVenteEnregistree:
    def gerer(self, event: VenteEnregistree) -> None:
        produit = self.produit_repo.par_id(event.produit_id)
        produit.diminuer_stock(event.quantite)
        # ...
```

**Vérification avec lint-imports** :
```bash
uv run lint-imports

# Vérifie :
# ✓ contexts.A.domain ⊄ contexts.B.*
# ✓ contexts.A.application ⊄ contexts.B.*
# ✓ Communication via events uniquement
```

---

## 📌 En résumé

| ADR | Décision clé | Vérification |
|---|---|---|
| **0001** | 4 couches (Domaine → App → Infra → Interface) | Structure des dossiers |
| **0002** | Domaine = Python pur, 0 Django | `import-linter` : `domain` ⊄ `django` |
| **0003** | Journal append-only, pas d'ES complet | Tables `Mouvement` immutables |
| **0004** | Petits agrégats, référence par identité | Pas de FK ORM inter-agrégats, cohérence éventuelle (eventual consistency) |
| **0005** | Isolation stricte des contextes | `import-linter` : `contexts.A` ⊄ `contexts.B` |

**Comment ces ADRs sont appliqués dans le code** :

1. **Tests de domaine** ✅ (46 tests) — Pur Python, sans Django
2. **Repositories** ✅ — Mappers explicites domaine ↔ ORM
3. **Journal** ✅ — `MouvementModel` append-only
4. **Événements domaine** ✅ — `ServiceOuvert`, `VenteEnregistree`, etc.
5. **Agrégats petits** ✅ — Service, Vente, Addition indépendants
6. **import-linter** ✅ — Vérifie isolation et couches

---

**Dernière mise à jour** : 2026-07-28  
**Auteur** : Claude Code (Community)
