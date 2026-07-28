# 🏢 Domaines métier

Chaque domaine (ou *Bounded Context*) en DDD est documenté ici avec ses fonctionnalités.

## Domaines disponibles

### ✅ [Service & Ventes](./service-ventes/)

**État** : 10 fonctionnalités livrées  
**Contexte** : Gestion des services, ventes, additions et règlements  
**Prochaines étapes** : Stock & Inventaire (l'ancre anti-vol)

- [Ouvrir un service](./service-ventes/01-ouvrir-un-service.md)
- [Enregistrer une vente](./service-ventes/02-enregistrer-une-vente.md)
- [Clôturer un service](./service-ventes/03-cloturer-un-service.md)
- [Ouvrir une addition](./service-ventes/04-ouvrir-une-addition.md)
- [Régler une addition](./service-ventes/05-regler-une-addition.md)
- [Rattacher une vente à une addition](./service-ventes/06-rattacher-une-vente-a-une-addition.md)
- [Encaisser un paiement (partiel ou total)](./service-ventes/07-encaisser-un-paiement.md)
- [Sous-caisse serveuse (réconciliation)](./service-ventes/08-sous-caisse-serveuse.md)

### Crédit & Créances

- [Crédit client](./credit-creances/01-credit-client.md)

[Voir le domaine complet →](./service-ventes/)

---

### 📋 [Stock & Inventaire](./stock-inventaire/) — À développer

**État** : 🟡 Design, pas encore implémenté  
**Contexte** : Pleins/vidanges, inventaire, mouvements de stock

---

### 📋 [Crédit & Créances](./credit-creances/) — À développer

**État** : 🟡 Design, pas encore implémenté  
**Contexte** : Clients, crédit, politique de crédit, remboursements

---

### 📋 [Approvisionnement](./approvisionnement/) — À développer

**État** : 🟡 Design, pas encore implémenté  
**Contexte** : Livraisons, fournisseurs, consignes valorisées

---

### 📋 [Catalogue & Tarification](./catalogue-tarification/) — À développer

**État** : 🟡 Design, pas encore implémenté  
**Contexte** : Produits, prix datés, conditionnements

---

### 🟢 [Gouvernance & Accès](./gouvernance-acces/) — Amorcé

**État** : authentification livrée ; acteurs, rôles et délégation restent à faire  
**Contexte** : Acteurs, rôles, délégation, validations

- [Authentifier les requêtes et attribuer les faits](./gouvernance-acces/01-authentifier-les-requetes.md)

---

### 📊 [Rapports & Consolidation](./rapports/) — À développer

**État** : 🟡 Design, pas encore implémenté  
**Contexte** : Projections, dashboards, rapports multi-bar

---

## 📖 Comment lire cette documentation

### Pour une fonctionnalité

1. **En haut** : Vue d'ensemble (acteur, déclencheur, résultat)
2. **Flux principal** : Diagramme ASCII du cas d'usage
3. **Contrats API** : Entrée (Command) et Sortie (DTO)
4. **Invariants** : Règles métier non négociables
5. **Événement domaine** : Event Sourcing
6. **Erreurs** : Codes HTTP et exceptions
7. **Exemple curl** : Copier-coller prêt pour tester localement
8. **Chemins de test** : Où trouver les tests automatisés

### Pour un domaine complet

- Lisez le **README.md** du domaine (architecture, patterns, métriques)
- Parcourez les fonctionnalités listées
- Consultez [../tests/<domaine>/](../tests/) pour la suite de tests

---

## 🚀 Ajouter une nouvelle fonctionnalité

### 1. Créer la doc

Dans `docs/domaines/<domaine>/`, créer un nouveau fichier :
```
0X-nom-de-la-fonctionnalite.md
```

Utiliser le template :
```markdown
# Fonctionnalité : [Nom]

## Vue d'ensemble
...

## Flux principal
...

## Contrats API
...

## Invariants
...

## Événement domaine produit
...

## Erreurs possibles
...

## Exemple local (curl)
...

## Chemins de test
...
```

### 2. Implémenter la fonctionnalité

Suivre la structure verticale (domaine → application → infrastructure → interface) :

```
Backend/contexts/<domaine>/
├── domain/
│   ├── mon_concept.py          (nouveau agrégat)
│   ├── events.py               (nouveau événement)
│   └── exceptions.py           (nouvelle exception)
├── application/
│   ├── use_cases/
│   │   └── faire_quelquechose.py (nouveau handler)
│   └── dto.py                  (nouvelle command + DTO)
├── infrastructure/
│   ├── django_app/
│   │   └── models.py           (nouveau modèle ORM)
│   └── persistence/
│       ├── repository.py       (nouvelle méthode)
│       └── mapper.py           (nouveau mapping)
├── interface/rest/
│   ├── views.py                (nouveau endpoint)
│   ├── serializers.py          (nouveau serializer)
│   └── urls.py                 (nouvelle route)
└── tests/
    ├── test_concept_domain.py  (domaine pur)
    ├── test_faire_quelquechose_handler.py (app)
    └── test_faire_quelquechose_api.py (intégration)
```

### 3. Ajouter les tests

Tests en pyramide (3 niveaux) :

```python
# 1. Domaine pur (pas de Django)
def test_concept_invariant():
    """Domaine : règle métier fondamentale."""
    assert ...

# 2. Handler (orchestration + persistance)
def test_handler_persiste_et_journalise():
    """Application : fakes en mémoire."""
    assert repository.par_id(id) is not None
    assert journal.evenements[-1].type == ...

# 3. API (bout en bout)
def test_api_endpoint_retourne_201():
    """Interface : HTTP réel."""
    response = client.post("/api/...", data={...})
    assert response.status_code == 201
```

### 4. Mettre à jour docs/tests/<domaine>/README.md

Ajouter les tests dans la section appropriée :

```markdown
## Fonctionnalité N : [Nom]

### Tests domaine
...

### Tests handler
...

### Tests API
...
```

---

## 📊 Checklist avant de merger

- [ ] Fonctionnalité documentée dans `docs/domaines/<domaine>/0X-*.md`
- [ ] Tests documentés dans `docs/tests/<domaine>/README.md`
- [ ] Tests locaux passent : `uv run pytest`
- [ ] Quality gate : `bash validate.sh`
- [ ] Commits en Conventional Commits : `feat(domaine): message`
- [ ] PR ouverte avec titre et description
- [ ] Exemple curl fonctionne en local

---

## 🔗 Références

- **Modèle métier complet** : [../02-modele-metier.md](../02-modele-metier.md)
- **Architecture backend** : [../03-architecture-backend.md](../03-architecture-backend.md)
- **ADRs & décisions** : [../decisions/](../decisions/)
- **Guide de contribution** : [../../CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**Dernière mise à jour** : 2026-07-28  
**Auteur** : Claude Code (Community)
