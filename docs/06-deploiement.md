# 06 — Déploiement et outillage

Deux choses distinctes, souvent confondues :

- **Render** fait tourner l'API et sa base de données. C'est la production.
- **docker-compose**, sur votre machine, fournit une base de développement et
  les interfaces d'administration (pgAdmin, Portainer). Rien de tout cela ne
  part en ligne.

---

## 1. La chaîne de déploiement

```
git push (main)
      │
      ▼
GitHub Actions — job « backend »
  ruff · ruff format · mypy strict · import-linter · pytest · pip-audit
      │
      │  ✗ rouge  →  rien ne part. Fin.
      ▼  ✓ vert
GitHub Actions — job « deploy »
  POST vers le Deploy Hook Render
      │
      ▼
Render : build (uv sync → collectstatic → migrate) puis démarrage gunicorn
```

Le job de déploiement ne s'arrête pas à l'appel du hook : il **interroge
`/api/sante/` jusqu'à y lire le commit attendu**. Sans cela, il se déclarait vert
sur la seule réponse `sync started` de Render — ce qui est arrivé sur la PR #56,
où la production a servi l'ancienne version pendant près d'une heure derrière un
pipeline tout vert.

Le point important est `autoDeploy: false` dans [`render.yaml`](../render.yaml).
Par défaut Render déploie dès qu'il voit un commit, **sans attendre la CI**. On
le désactive pour que le seul chemin vers la production passe par la quality
gate. Un test rouge bloque donc réellement la mise en ligne.

### Mise en service (une seule fois)

1. **Créer le Blueprint.** Sur Render : *New → Blueprint*, pointer ce dépôt.
   Render lit `render.yaml` et crée le service `siptrack-api` et la base
   `siptrack-db`. `SECRET_KEY` est généré par Render ; il n'apparaît nulle part
   dans le dépôt.

2. **Récupérer le Deploy Hook.** Service `siptrack-api` → *Settings* →
   *Deploy Hook*. Copier l'URL. **Elle vaut un droit de déploiement : elle se
   traite comme un mot de passe.**

3. **Déclarer le secret GitHub.** Dépôt → *Settings* → *Secrets and variables* →
   *Actions* → *New repository secret* :
   - nom : `RENDER_DEPLOY_HOOK_URL`
   - valeur : l'URL copiée

4. *(facultatif)* Variable `RENDER_SERVICE_URL` avec l'adresse publique du
   service : GitHub l'affiche alors comme lien de l'environnement `production`.

Tant que le secret n'existe pas, le job `deploy` **n'échoue pas** : il s'arrête
avec un avertissement visible dans le résumé de l'exécution. La CI reste verte,
mais rien n'est déployé. C'est délibéré — un dépôt fraîchement cloné ne doit pas
avoir une CI rouge pour une raison de configuration.

### Ce que fait le build

[`Backend/render-build.sh`](../Backend/render-build.sh) — `set -euo pipefail`,
donc la moindre commande en échec arrête le build :

| Étape | Rôle |
|---|---|
| `uv sync --locked --no-dev --no-build` | Dépendances au lockfile, sans les outils de dev, roues précompilées uniquement |
| `manage.py collectstatic` | Assets de l'admin Django et de Swagger, servis ensuite par WhiteNoise |
| `manage.py migrate` | Schéma de base à jour avant que la nouvelle version ne réponde |

### Réglages de production

[`config/settings/prod.py`](../Backend/config/settings/prod.py) :

- `ALLOWED_HOSTS` est relu depuis la variable brute, **sans** passer par le
  schéma de `base.py` — celui-ci porte les valeurs de développement
  (`localhost`, `127.0.0.1`), qui n'ont rien à faire en production. L'hôte
  `.onrender.com` s'ajoute seul via `RENDER_EXTERNAL_HOSTNAME`.
- **WhiteNoise** sert les fichiers statiques depuis le processus applicatif :
  il n'y a pas de nginx devant sur Render. Sans lui, l'admin et Swagger
  arriveraient sans CSS.
- Empreinte + compression sur les statiques (`CompressedManifestStaticFilesStorage`) :
  le cache navigateur peut être agressif sans jamais servir une version périmée.

---


## ⚠️ Le deploy hook doit être celui du **service**, pas du Blueprint

Render propose deux hooks, et l'un des deux ne déploie rien.

| Hook | Réponse | Effet |
|---|---|---|
| **Blueprint** (`exs-…`) | `sync started, …/blueprint/…/sync/` | relit `render.yaml` — **ne déploie pas le code** |
| **Service** (`srv-…`) | `{"deploy":{"id":"dep-…"}}` | déclenche un vrai build ✅ |

Un hook de Blueprint qui ne trouve aucun changement dans `render.yaml` **n'a rien
à faire** : il répond « sync started » et s'arrête. Le job de CI se déclarait
alors vert, et la production restait sur l'ancienne version.

**C'est arrivé, et c'est passé inaperçu quatre PR d'affilée** : l'idempotence
(#56), le health check (#58) et le durcissement sécurité (#60) sont restés hors
ligne pendant que le pipeline affichait tout vert.

### Récupérer le bon hook

1. Render → **`siptrack-api`** → **Settings** → **Deploy Hook**
2. L'URL contient **`srv-`**. Si elle contient `exs-`, c'est le Blueprint : mauvais hook.
3. GitHub → **Settings** → **Secrets and variables** → **Actions**
4. Remplacer `RENDER_DEPLOY_HOOK_URL`

La CI refuse désormais un hook de Blueprint dès la première réponse, avec la
marche à suivre dans le résumé du job — plutôt que d'attendre dix minutes un
déploiement qui ne viendra pas.


## 2. Outillage local

```bash
cp .env.docker.example .env.docker   # puis remplacer les mots de passe
docker compose --env-file .env.docker up -d
```

| Service | Adresse | Rôle |
|---|---|---|
| PostgreSQL | `127.0.0.1:5432` | Base de développement |
| pgAdmin | <http://127.0.0.1:5050> | Administration SQL |
| Portainer | <https://127.0.0.1:9443> | Administration des conteneurs |

Tout est publié sur `127.0.0.1` uniquement : rien n'est joignable depuis le
réseau local. Le fichier `.env.docker` refuse de démarrer sans mots de passe
explicites — aucun compte par défaut ne traîne.

### Brancher pgAdmin sur la base locale

*Add New Server* → onglet *Connection* :
`Host` = `postgres` (le nom du service dans le réseau Compose), `Port` = `5432`,
puis les identifiants de `.env.docker`.

### Brancher pgAdmin sur la base Render

Render → base `siptrack-db` → *Connections* → **External Database URL**. Elle
contient hôte, port, base, utilisateur et mot de passe. Cocher **SSL requis**.

> Vous administrez alors la production. Une requête `UPDATE` ou `DELETE` sans
> `WHERE` y est définitive, et le journal d'événements ne la rattrapera pas :
> il enregistre les faits émis par l'application, pas les écritures faites
> directement en SQL.

### Portainer et Render

Portainer pilote un démon Docker par son socket. Render n'expose pas le socket
Docker de ses hôtes : **Portainer ne pourra jamais gérer vos services Render.**
Il gère vos conteneurs locaux, ce pour quoi il est fait. Pour la production,
l'observation passe par le tableau de bord Render.

> Monter `/var/run/docker.sock` donne à Portainer le contrôle total du démon,
> donc l'équivalent de `root` sur la machine. C'est inhérent à l'outil. D'où la
> publication sur `127.0.0.1` seulement, et un mot de passe administrateur
> solide à la première connexion.

---

## 3. Reste à faire

- ~~Aucun health check applicatif~~ — **livré**. `GET /api/sante/` rend le
  commit servi et éprouve l'accès à la base par une requête réelle. La décision
  de sécurité qui bloquait est tranchée : le dépôt est public, donc publier le
  commit ne révèle rien.
- **Pas de sauvegarde automatisée** de la base.
- **Pas de retour arrière outillé.** Render sait redéployer un commit antérieur,
  mais une migration déjà appliquée ne se défait pas toute seule.
- **Le plan gratuit met le service en veille** après une période d'inactivité :
  la première requête suivante attend le réveil. Acceptable en démonstration,
  pas pour un bar en service.
