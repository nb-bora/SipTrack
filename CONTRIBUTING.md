# Contribuer à SipTrack

## Guide pour les contributeurs

Merci de contribuer ! Ce guide vous aide à suivre nos standards de qualité.

### Avant de commencer

1. **Lisez la documentation** : [docs/README.md](docs/README.md) et [Backend/README.md](Backend/README.md)
2. **Regardez les ADR** : [docs/decisions/](docs/decisions/) pour comprendre les choix d'architecture
3. **Comprenez le modèle métier** : [docs/02-modele-metier.md](docs/02-modele-metier.md)

### Flux de développement

#### 1. **Créer une branche**

```bash
git checkout main
git pull origin main
git checkout -b feat/mon-feature
```

Nommage des branches :
- `feat/<verbe>-<objet>` : nouvelles fonctionnalités (`feat/ouvrir-addition`)
- `fix/<issue>` : corrections de bugs
- `refactor/<zone>` : refactorisation
- `test/<zone>` : ajouts de tests
- `docs/<sujet>` : documentation
- `chore/<sujet>` : maintenance

#### 2. **Développer & tester localement**

```bash
cd Backend
uv sync                    # Installez les dépendances
uv run pytest             # Lancez les tests
uv run ruff check .       # Vérifiez le lint
uv run ruff format .      # Formatez le code
uv run mypy .             # Vérifiez le typage
uv run lint-imports       # Vérifiez l'architecture
```

**Important** : le code doit passer **tous les checks** avant un commit.

#### 3. **Commitez avec Conventional Commits**

Format : `<type>(<scope>): <description>`

```bash
git commit -m "feat(service_ventes): ouvrir une addition sur un service"
git commit -m "test(addition): parametrer le statut initial"
git commit -m "fix(repositories): ajouter methode mettre_a_jour"
```

Types acceptés :
- `feat` : nouvelle fonctionnalité
- `fix` : correction de bug
- `test` : ajout ou modification de tests
- `refactor` : refactorisation
- `style` : formatage, imports
- `chore` : maintenance, dépendances
- `docs` : documentation

Scopes disponibles :
- `service_ventes` : bounded context « Service & Ventes »
- (autres contextes selon le développement)

#### 4. **Pushez et ouvrez une PR**

```bash
git push -u origin feat/mon-feature
gh pr create --title "feat(service_ventes): description" \
  --body "## Résumé\n...\n## Tests\n..."
```

### Critères de qualité

Votre PR **doit** passer :

✅ **Linting** (`ruff check`)
✅ **Formatage** (`ruff format --check`)
✅ **Typage strict** (`mypy .`)
✅ **Architecture** (`lint-imports`)
✅ **Tests** (`pytest` — couverture ≥ 85%)
✅ **Dépendances** (`pip-audit`)
✅ **SonarCloud** (duplication < 20%, complexité OK)

### Structure d'une tranche verticale (recommandé)

Une bonne PR implémente un cas d'usage **de bout en bout** :

```
Domaine (pure, 0 Django)
    ↓
Application (orchestration, ports)
    ↓
Infrastructure (persistance Django)
    ↓
Interface REST (vues, sérializers)
```

**Fichiers minimaux** :

```
domain/
  - nouveau_concept.py (agrégat, enums, events)
application/
  - use_cases/faire_quelquechose.py (handler)
  - dto.py (commands + DTOs)
infrastructure/
  - django_app/models.py (ORM)
  - persistence/repository.py (concrète)
  - persistence/mapper.py (traduction)
interface/rest/
  - views.py (vues)
  - serializers.py (sérializers)
  - urls.py (routes)
tests/
  - test_concept_domain.py (domaine pur)
  - test_faire_quelquechose_handler.py (app isolée)
  - test_faire_quelquechose_api.py (intégration)
config/
  - container.py (wiring)
```

### Tests : la pyramide

```
Intégration (API, endpoint-to-endpoint)
    ↓
Application (handler + fakes)
    ↓
Domaine (pur, pas de Django) ← MAJORITÉ
```

**Minimums** :
- Tests de domaine : logique métier, cycles de vie, invariants
- Tests de handler : persistance, journalisation, exceptions
- Tests API : codes HTTP, cas d'erreur, round-trips

### Code — Règles du projet

#### Domaine
- ✅ Python pur (0 `import django`, 0 `import rest_framework`)
- ✅ Immutabilité des Value Objects
- ✅ Events au passé : `ServiceOuvert`, `VenteEnregistree`
- ✅ Exceptions avec identifiants (ex. `ServiceIntrouvable(service_id)`)
- ✅ Pas de commentaires sauf si la **raison** n'est pas évidente

#### Application
- ✅ Handlers : `<Verbe><Objet>Handler` (ex. `OuvrirServiceHandler`)
- ✅ Methods : `executer(commande: Command) -> DTO`
- ✅ DTOs figés : `@dataclass(frozen=True)`
- ✅ Ports du domaine injectés (UnitOfWork, Repository, Journal, Clock)

#### Infrastructure
- ✅ ORM : tables séparant des agrégats (pas de FK inter-contextes)
- ✅ Mappers : `vers_ligne()` (domaine → ORM), `vers_domaine()` (ORM → domaine)
- ✅ Repos : méthodes alignées sur le port de domaine

#### Interface
- ✅ Serializers explicites (jamais `ModelSerializer`)
- ✅ Vues simples : valider + mapper + déléguer + sérialiser
- ✅ Codes HTTP idempotents : 201 pour création, 200 pour GET, 404/409 sur erreurs

### Avant de demander une revue

Checklist finale :

- [ ] Tests locaux passent (`uv run pytest`)
- [ ] Lint/format propres (`uv run ruff check . && uv run ruff format .`)
- [ ] Types OK (`uv run mypy .`)
- [ ] Architecture respectée (`uv run lint-imports`)
- [ ] Pas d'imports inutilisés
- [ ] Pas de `print()` ou `TODO` dans le code
- [ ] Commit messages clairs (Conventional Commits)
- [ ] Branche à jour avec `main`

### Questions ?

Consultez :
- **Architecture** : [docs/03-architecture-backend.md](docs/03-architecture-backend.md)
- **Domaine métier** : [docs/02-modele-metier.md](docs/02-modele-metier.md)
- **Décisions** : [docs/decisions/](docs/decisions/)
- **Code existant** : regardez les PRs mergées ou les tests

---

**Merci de respecter ces standards.** Ils gardent le code propre, maintenable et conforme à notre architecture. 🙌
