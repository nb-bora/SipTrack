# SipTrack — Backend

API Django (DDD + Clean Architecture). Voir la référence complète dans
[`../docs/`](../docs/) : [modèle métier](../docs/02-modele-metier.md),
[architecture](../docs/03-architecture-backend.md), [ADR](../docs/decisions/).

## Pré-requis

- [uv](https://docs.astral.sh/uv/) (gère Python, l'environnement et les dépendances)
- Python 3.13 (installé automatiquement par uv si besoin)
- **PostgreSQL 15+**, accessible et avec une base dédiée

## Démarrage

```bash
cd Backend
cp .env.example .env            # renseigner SECRET_KEY et les variables DB_*
uv sync                         # crée le venv + installe tout (dont le groupe dev)
uv run manage.py migrate        # applique les migrations
uv run manage.py runserver      # http://127.0.0.1:8000
```

### Base de données

PostgreSQL est utilisé **en dev comme en prod** : on ne veut pas découvrir en
production les différences de comportement de SQLite. Créer la base une fois :

```bash
createdb -h 127.0.0.1 -U <DB_USER> siptrack
```

La connexion est pilotée par `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` /
`DB_PASSWORD` (voir `.env.example`). Fournir `DATABASE_URL` prend le pas sur ces
variables — c'est la forme utilisée en production.

Les tests créent et détruisent leur propre base `test_<DB_NAME>` : le rôle
utilisé doit avoir le droit `CREATEDB`.

## Documentation de l'API (Swagger)

Serveur démarré :

| URL | Quoi |
|---|---|
| http://127.0.0.1:8000/api/doc/ | **Swagger UI** — essayer les routes depuis le navigateur |
| http://127.0.0.1:8000/api/redoc/ | ReDoc — lecture du contrat |
| http://127.0.0.1:8000/api/schema/ | Schéma OpenAPI 3 brut (YAML) |

Pour appeler les routes depuis Swagger : cliquer **Authorize** et saisir
`Token <votre-jeton>` (voir la section suivante pour l'obtenir).

En développement, la doc est ouverte ; ailleurs elle exige un jeton — la carte
complète de l'API n'a pas à être publique. Les assets sont servis en local, donc
tout fonctionne sans réseau.

## Authentification

**Toutes les routes exigent un jeton.** L'auteur d'un Fait est déduit du compte
authentifié, jamais du corps de la requête : sans cela, n'importe qui pourrait signer
au nom de n'importe qui et le journal ne prouverait rien.

Créer un compte, puis obtenir un jeton :

```bash
uv run manage.py createsuperuser        # ou createuser via l'admin Django

curl -X POST http://127.0.0.1:8000/api/auth/jeton/ \
  -H "Content-Type: application/json" \
  -d '{"username":"serveuse1","password":"..."}'
# {"token":"9c8f..."}
```

Le jeton se présente ensuite sur chaque appel :

```bash
curl http://127.0.0.1:8000/api/services/<id>/ -H "Authorization: Token 9c8f..."
```

Le jeton n'expire pas (l'app mobile est offline-first) ; il se révoque en supprimant
la ligne correspondante dans l'admin. La route d'obtention est limitée en débit
(`THROTTLE_OBTENTION_JETON`, 10/min par défaut) contre le bourrinage.

## Tranche verticale disponible

`Ouvrir un service` de bout en bout (domaine → application → infrastructure → interface) :

```bash
JETON=9c8f...

# Ouvrir un service
curl -X POST http://127.0.0.1:8000/api/services/ \
  -H "Authorization: Token $JETON" \
  -H "Content-Type: application/json" \
  -d '{"bar_id":"bar1","capacite":"operatrice","fond_de_caisse":10000}'

# Lire un service
curl http://127.0.0.1:8000/api/services/<id>/ -H "Authorization: Token $JETON"
```

## Qualité

```bash
uv run pytest              # tests (domaine pur + API d'intégration)
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy .              # typage
uv run lint-imports        # contrats d'architecture (import-linter)
```

## Structure (rappel)

```
Backend/
├── config/            # settings, urls, composition root (container.py)
├── shared/            # domain (VO, events) + application (ports)
└── contexts/
    └── service_ventes/
        ├── domain/            # agrégats, VO, events, repositories (interfaces) — PYTHON PUR
        ├── application/       # use cases (Service Layer), DTO
        ├── infrastructure/    # ORM Django, repos concrets, journal, UoW
        └── interface/rest/    # DRF : vues, serializers (DTO), urls
```

Règle d'or : le **domaine n'importe jamais Django** — garanti par `import-linter`.
