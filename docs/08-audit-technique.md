# 08 — Audit technique

**Date** : 2026-07-29 · **Périmètre** : Backend (`main`) · **Barre d'exigence** : *pouvoir servir des millions d'utilisateurs*

> **Sur la méthode.** Chaque constat ci-dessous a été **mesuré ou lu dans le code**, jamais supposé. Quand une affirmation n'a pas pu être vérifiée, c'est écrit. Cette précaution n'est pas rhétorique : l'audit précédent ([07](./07-audit-securite.md)) contenait trois affirmations fausses.
>
> **Le prompt d'audit visait FastAPI, SQLAlchemy et Pydantic.** Le projet est **Django + DRF + ORM Django**. Les sections correspondantes ont été transposées, pas inventées.

---

## Verdict

| | |
|---|---|
| **Score global** | **58 / 100** |
| Pour un pilote de quelques bars | ✅ viable |
| Pour des milliers d'utilisateurs | ⚠️ à retravailler |
| **Pour des millions** | ❌ **l'architecture actuelle l'interdit** |

L'écart ne vient pas de la qualité du code — qui est **au-dessus de la moyenne** — mais de **deux décisions structurelles** qui plafonnent le débit à quelques requêtes par seconde, quel que soit le matériel.

### Scores par domaine

| Domaine | Score | Commentaire |
|---|---|---|
| **Architecture** | 85 | DDD réel, contrats vérifiés par outil |
| **Maintenabilité** | 82 | ADR nourris, nommage métier, tests lisibles |
| Qualité de code | 72 | Sonar A partout, 0,3 % de duplication — **couverture jamais mesurée** |
| Base de données | 70 | Contraintes solides, immuabilité par trigger — index manquants |
| Dette technique | 68 | Faible en surface, lourde en structure |
| API | 66 | Cohérente, idempotente — sans pagination ni versioning |
| **Sécurité** | 62 | Autorisation solide — **clé de repli, aucun débit limité** |
| DevOps | 48 | CI sérieuse mais mensongère jusqu'à ce jour |
| **Performance** | 35 | N+1 mesuré, aucun cache, aucune pagination |
| **Scalabilité** | **18** | **Verrou global + un seul worker** |

---

## Les deux verrous structurels

### 🔴 A1 — Le journal sérialise toutes les écritures de la plateforme

**Catégorie** : Scalabilité / Architecture · **Gravité : CRITIQUE**
**Localisation** : `shared/infrastructure/journal/adapter.py:22` — `DjangoJournal.enregistrer`

```python
def enregistrer(self, evenements, *, auteur_id):
    self._verrouiller_la_chaine()      # verrou consultatif GLOBAL
    precedent = MouvementModel.objects.order_by("-sequence").first()
```

Le commentaire du code le dit lui-même : ce verrou sérialise « **deux services simultanés (deux bars, deux serveuses)** ».

**Le problème** : le chaînage d'empreintes impose un ordre total sur **l'ensemble de la plateforme**. Deux bars situés dans deux villes, sans le moindre rapport, **s'attendent l'un l'autre** pour enregistrer une vente.

**Impact** : le débit d'écriture maximal de tout le système = `1 / durée_d_une_transaction_journal`. Ajouter des serveurs n'y change **rien** — c'est la définition d'un goulet non parallélisable.

| Bars actifs simultanément | Comportement attendu |
|---|---|
| 1–5 | imperceptible |
| ~50 | attente visible en heure de pointe |
| ~500 | file d'attente, expirations |
| des milliers | **le système ne fonctionne pas** |

**Norme** : Amdahl ; AWS Well-Architected — *Performance Efficiency*, éviter la coordination globale.

**Correction** : **une chaîne par bar**. La propriété recherchée — un registre inaltérable et opposable — est *par bar*, pas globale. Personne n'a besoin de prouver l'ordre relatif d'une vente à Douala et d'une vente à Yaoundé.

```python
# sequence et empreinte_precedente deviennent relatives au bar
MouvementModel.objects.filter(bar_id=bar_id).order_by("-sequence").first()
# verrou porté par le bar : pg_advisory_xact_lock(hashtext(bar_id))
```

Le `MouvementModel` n'a **pas** de colonne `bar_id` aujourd'hui — c'est l'essentiel du travail (migration + rétro-remplissage + recalcul des empreintes).

**Priorité : 1** · **Effort : Élevé** (3–5 j)

---

### 🔴 A2 — Un seul worker, synchrone : une requête à la fois

**Catégorie** : Scalabilité / DevOps · **Gravité : CRITIQUE**
**Localisation** : `render.yaml:20`

```yaml
startCommand: "... gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
```

Aucun `--workers`, aucun `--threads`. Les journaux Render le confirment :

```
==> Setting WEB_CONCURRENCY=1 by default, based on available CPUs
[INFO] Using worker: sync
```

**Un worker synchrone traite une requête à la fois.** La deuxième attend. Sur le plan gratuit (0,1 CPU), c'est la limite matérielle autant que logicielle.

**Impact** : quelques requêtes par seconde au mieux ; toute requête lente bloque toutes les autres.

**Correction** : `--workers $(( 2 * CPU + 1 )) --threads 4 --timeout 60`, et quitter le plan gratuit. Sans A1 corrigé, l'ajout de workers ne fera que déplacer la contention sur le verrou.

**Priorité : 2** · **Effort : Faible** (1 h) — mais **sans effet tant que A1 tient**

---

## Sécurité

### 🔴 S1 — La production démarre avec une clé de repli publique

**Gravité : CRITIQUE** · `config/settings/base.py:21`

```python
SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-override-me")
```

**Vérifié** : en retirant la variable d'environnement, l'application démarre **sans un mot** avec la clé de repli. **Le dépôt est public** : cette valeur est lisible par tous.

Render l'alimente aujourd'hui (`generateValue: true`), donc l'exposition n'est pas active. Mais un nouvel environnement, un Blueprint restauré ou une variable effacée suffirait — **et rien ne le signalerait**.

Conséquence si cela arrivait : signature des jetons, des cookies et des jetons de réinitialisation dérivée d'une clé connue → **falsification possible**.

**Normes** : OWASP A02:2021 *Cryptographic Failures* · CWE-798 *Hardcoded Credentials* · Django Deployment Checklist.

**Correction** — refuser de démarrer :

```python
# prod.py
SECRET_KEY = os.environ["SECRET_KEY"]   # KeyError explicite au demarrage
```

**Priorité : 1** · **Effort : Faible** (15 min)

---

### 🟠 S2 — Aucune limitation de débit, sauf sur l'obtention du jeton

**Gravité : ÉLEVÉE** · `config/settings/base.py:155`

```python
"DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
"DEFAULT_THROTTLE_RATES": {"obtention_jeton": "10/min"},
```

`ScopedRateThrottle` **ne s'applique qu'aux vues portant un `throttle_scope`**. Une seule le porte. **Tout le reste de l'API est sans limite** : ventes, paiements, lectures, tout.

**Impact** : un jeton valide suffit à saturer le worker unique (cf. A2). Avec le verrou global (A1), **un seul client abusif bloque la plateforme entière**.

**Normes** : OWASP API4:2023 *Unrestricted Resource Consumption*.

**Correction** :

```python
"DEFAULT_THROTTLE_CLASSES": [
    "rest_framework.throttling.UserRateThrottle",
    "rest_framework.throttling.AnonRateThrottle",
],
"DEFAULT_THROTTLE_RATES": {
    "user": "300/min", "anon": "20/min", "obtention_jeton": "10/min",
},
```

⚠️ Le compteur DRF s'appuie sur le **cache**. Sans cache partagé configuré, il est *par processus* — inopérant dès qu'il y a plusieurs workers. Redis devient nécessaire.

**Priorité : 3** · **Effort : Moyen**

---

### 🟠 S3 — Jetons sans expiration ni rotation

**Gravité : ÉLEVÉE** · `config/settings/base.py:148`

`rest_framework.authentication.TokenAuthentication` produit un jeton **opaque, permanent**. Il n'expire jamais, ne tourne pas, et ne peut être révoqué qu'en le supprimant en base.

**Impact** : un téléphone volé — scénario **courant** pour l'usage visé — donne un accès permanent. Aucune déconnexion, aucune expiration de session.

**Normes** : OWASP API2:2023 *Broken Authentication* · NIST SP 800-63B.

**Correction** : jetons courts + jeton de rafraîchissement (`djangorestframework-simplejwt`), ou expiration + rotation sur le jeton DRF. Prévoir une **révocation par appareil**.

**Priorité : 5** · **Effort : Moyen**

---

### 🟠 S4 — Aucune pagination : une réponse peut être arbitrairement grosse

**Gravité : ÉLEVÉE** · aucun `PAGE_SIZE` configuré ; `EncoursListView`, `CatalogueListView`, `BarListCreateView`, `ProduitListView`

`GET /api/bars/{id}/encours/` rend **tous** les clients endettés. Un bar à 5 000 clients renvoie 5 000 objets imbriqués, chacun avec ses créances.

**Impact** : mémoire du worker, temps de sérialisation, taille de réponse — et cela **bloque le worker unique** pendant tout ce temps.

**Normes** : OWASP API4:2023.

**Correction** : `PageNumberPagination` avec `PAGE_SIZE` par défaut et un maximum imposé.

**Priorité : 4** · **Effort : Moyen** — casse le contrat publié, à faire **avant** qu'un client existe

---

### ✅ Ce qui est solide, et vérifié

| Vecteur | État |
|---|---|
| Injection SQL | ✅ ORM partout, **zéro** SQL concaténé |
| Command injection, désérialisation | ✅ ni `subprocess`, ni `eval`, ni `pickle` — vérifié |
| XXE, LDAP, Path traversal | ✅ sans objet : pas d'XML, pas de LDAP, pas de service de fichiers |
| Upload de fichiers | ✅ sans objet : aucun endpoint d'upload |
| CSRF | ✅ jeton dans l'en-tête, pas de cookie de session sur l'API |
| XSS | ✅ API JSON uniquement, sérialisation DRF |
| IDOR / cloisonnement | ✅ **corrigé et éprouvé** ([ADR-0006](./decisions/0006-autorisation-a-la-frontiere.md)) |
| Élévation de privilèges | ✅ capacités vérifiées ; comptes plateforme en lecture seule ([ADR-0007](./decisions/0007-comptes-plateforme.md)) |
| Rejeu | ✅ **corrigé** ([ADR-0009](./decisions/0009-idempotence-des-ecritures.md)) |
| Secrets en dur | ✅ aucun — **hors** la clé de repli (S1) |
| Logs sensibles | ✅ corps de requête **jamais** journalisés, test à l'appui |
| En-têtes HTTP | ✅ HSTS, SSL redirect, cookies sécurisés |
| Mots de passe | 🟡 PBKDF2 (défaut Django) — Argon2 préférable |

---

## Performance

### 🟠 P1 — N+1 mesuré sur les encours

**Gravité : ÉLEVÉE** · `contexts/credit_creances/infrastructure/persistence/encours.py:23`

```python
def tous(self, bar_id):
    return tuple(self._encours(client)              # 1 requete PAR client
                 for client in ClientModel.objects.filter(bar_id=bar_id))
```

**Mesure** (`CaptureQueriesContext`) :

| Clients endettés | Requêtes SQL |
|---|---|
| 1 | 4 |
| 3 | 6 |
| 6 | 9 |
| 10 | 13 |

Pente **exactement `N + 3`**. À 500 clients : **503 requêtes** — et sans pagination (S4), rien ne borne N.

**Correction** : une seule requête agrégée.

```python
CreditModel.objects
    .filter(client__bar_id=bar_id)
    .select_related("client")
    .annotate(total_rembourse=Sum("remboursements__montant"))
```

**Priorité : 6** · **Effort : Moyen**

---

### 🟡 P2 — `select_related` / `prefetch_related` : zéro occurrence

**Gravité : MOYENNE** · l'ensemble des couches de persistance

Aucun chargement anticipé nulle part. P1 est le cas mesuré ; les autres n'ont pas été éprouvés faute de jeux de données.

**Priorité : 8** · **Effort : Moyen**

### 🟡 P3 — Aucun cache

**Gravité : MOYENNE** · pas de `CACHES` configuré

Le catalogue et les capacités — lus à **chaque** requête — sont quasi immuables. Le contrôle d'accès interroge la base à chaque appel (une requête indexée, mesurée et bornée, mais une requête tout de même).

Redis devient de toute façon nécessaire pour S2.

**Priorité : 9** · **Effort : Moyen**

### 🟡 P4 — `bar_id` sans index sur `ServiceModel`

**Gravité : MOYENNE** · `contexts/service_ventes/infrastructure/django_app/models.py:14`

`CharField` nu. Catalogue et Crédit sont couverts par une contrainte unique composite `(bar_id, nom)` ; Service & Ventes ne l'est pas.

**Priorité : 7** · **Effort : Faible** (une migration)

---

## Architecture — le point fort

**Score : 85/100.** C'est réellement au-dessus de la moyenne, et il faut le préserver.

| Élément | Constat |
|---|---|
| Couches | domaine / application / infrastructure / interface, respectées |
| Domaine pur | **vérifié par outil** : aucun import Django ni DRF |
| Contextes isolés | **5 contrats `import-linter`, 0 violation** |
| Ports & adaptateurs | `TarifDuProduit`, `OuvertureDeCreance`, `ControleAcces` |
| Composition root | unique, explicite |
| Objets-valeurs | `Montant`, `Attribution`, `PrixDate` |
| Invariants | dans le domaine, pas dans les vues |
| Décisions | **9 ADR** motivés, y compris ce qu'ils ne couvrent pas |

**Ce que peu d'équipes font, et qui est fait ici** : les règles d'architecture sont **exécutables**. `lint-imports` échoue si un contexte en importe un autre. Ce n'est pas une convention, c'est un test.

### 🟡 AR1 — L'autorisation est à la frontière HTTP, pas dans le métier

**Gravité : MOYENNE** · `shared/interface/rest/acces.py`

Déjà assumé et écrit dans [ADR-0006](./decisions/0006-autorisation-a-la-frontiere.md) : une commande d'administration ou une tâche de fond **contournerait le garde**. La protection retenue est un test qui balaie les routes, pas un principe.

**Correction** : descendre le contrôle dans les cas d'usage le jour où un appelant non-HTTP apparaît.

**Priorité : 12** · **Effort : Élevé** (18 handlers)

### 🟡 AR2 — `MouvementModel` ignore le bar

**Gravité : MOYENNE** — c'est la cause racine de **A1**. Le journal, transverse, ne porte pas la dimension qui devrait le partitionner.

---

## Qualité, dette, maintenabilité

**SonarCloud** (branche `main`) :

| Métrique | Valeur | Lecture |
|---|---|---|
| Lignes de code | 10 643 | |
| Bugs / Vulnérabilités / Points chauds | **0 / 0 / 0** | |
| Notes Fiabilité / Sécurité / Maintenabilité | **A / A / A** | |
| Duplication | **0,3 %** | excellent |
| Dette technique | 52 min | *ne mesure que le code, pas la structure* |
| Complexité cognitive | 325 (≈ 1,4 / 100 lignes) | faible |
| Odeurs | 9 | négligeable |

**245 fonctions de test**, 249 cas exécutés.

### 🟠 Q1 — La couverture n'a jamais été mesurée

**Gravité : ÉLEVÉE**

`coverage.py` **n'est pas installé**. Sonar affiche `coverage: —`. Le nombre de tests est connu ; ce qu'ils atteignent ne l'est pas.

Or ce projet **repose** sur ses tests : le balayage des routes et l'inventaire du schéma sont ses garde-fous. Ne pas savoir ce qu'ils couvrent affaiblit précisément ce sur quoi tout repose.

**Correction** : `pytest-cov`, seuil d'échec, publication dans la CI.

**Priorité : 10** · **Effort : Faible**

> **Note.** Les 52 minutes de dette annoncées par Sonar sont **trompeuses**. Elles mesurent le code ligne à ligne. Elles ne voient ni le verrou global, ni le worker unique, ni le N+1 — soit **la totalité** de ce qui empêche ce système de monter en charge. Un outil ne remplace pas la lecture.

---

## DevOps

| Sujet | État |
|---|---|
| CI | ✅ ruff, mypy **strict**, import-linter, pytest, migrations |
| Actions épinglées par SHA | ✅ bon réflexe |
| Droits du workflow | ✅ minimum par job |
| Paquets sources interdits | ✅ `--only-binary` / `--no-build` |
| **`pip-audit`** | ❌ **n'a jamais tourné** — absent du `pyproject`, échec masqué par `continue-on-error`, résumé affichant une coche codée en dur (corrigé en cours) |
| **Déploiement constaté** | ❌ **non** — hook appelé ≠ version servie (#56 : une heure de décalage, pipeline vert) |
| Health check | ❌ absent (livré dans la PR en cours) |
| **Sauvegardes** | ❌ **aucune** |
| Retour arrière | ❌ aucune procédure ; migrations non réversibles |
| Alertes | ❌ personne n'est prévenu d'une panne |
| Plan | ⚠️ gratuit : mise en veille, base limitée |

### 🔴 D1 — Aucune sauvegarde de la base

**Gravité : CRITIQUE pour l'exploitation** · `docs/06-deploiement.md:145`

Le produit **est** un registre. Sa valeur entière tient dans ses données. Le journal inaltérable protège contre l'altération, **pas contre la perte** : un disque unique, sans copie, sans restauration éprouvée.

**Normes** : AWS Well-Architected — *Reliability*.

**Correction** : `pg_dump` planifié vers un stockage externe, **et une restauration réellement testée**. Une sauvegarde jamais restaurée n'est pas une sauvegarde.

**Priorité : 3** · **Effort : Moyen**

---

## Scalabilité — réponse chiffrée

| Palier | Verdict | Ce qui casse en premier |
|---|---|---|
| **10 000 utilisateurs** | ❌ | A2 (worker unique) puis A1 (verrou) |
| **100 000** | ❌ | A1 — infranchissable sans repartitionner le journal |
| **1 million** | ❌ | A1 + absence de cache, de pagination, de file d'attente |

**Ordre contraint** — chaque étape est inutile sans la précédente :

1. **A1** — chaîne par bar. *Sans cela, rien d'autre ne sert.*
2. **A2** — workers multiples. *Sans A1, ils se battent pour le verrou.*
3. **S4 + P1** — pagination et N+1. *Sans cela, chaque requête reste lourde.*
4. **P3** — Redis (cache + compteurs de débit).
5. Réplicas de lecture, file d'attente pour le journal, partitionnement.

> Aucun de ces travaux ne s'improvise sous charge. Le bon moment est **maintenant**, alors qu'aucun client n'existe encore.

---

## Les 20 problèmes prioritaires

| # | Problème | Gravité | Effort |
|---|---|---|---|
| 1 | **A1** — verrou global du journal | 🔴 Critique | Élevé |
| 2 | **S1** — clé de repli publique en production | 🔴 Critique | Faible |
| 3 | **D1** — aucune sauvegarde | 🔴 Critique | Moyen |
| 4 | **A2** — worker unique synchrone | 🔴 Critique | Faible |
| 5 | **S2** — aucune limitation de débit | 🟠 Élevé | Moyen |
| 6 | **S4** — aucune pagination | 🟠 Élevé | Moyen |
| 7 | **P1** — N+1 mesuré sur les encours | 🟠 Élevé | Moyen |
| 8 | **S3** — jetons sans expiration | 🟠 Élevé | Moyen |
| 9 | **Q1** — couverture non mesurée | 🟠 Élevé | Faible |
| 10 | Déploiement non constaté | 🟠 Élevé | Faible *(en cours)* |
| 11 | `pip-audit` jamais exécuté | 🟠 Élevé | Faible *(en cours)* |
| 12 | Aucune alerte sur panne | 🟠 Élevé | Moyen |
| 13 | **P4** — `bar_id` sans index | 🟡 Moyen | Faible |
| 14 | **P2** — aucun chargement anticipé | 🟡 Moyen | Moyen |
| 15 | **P3** — aucun cache | 🟡 Moyen | Moyen |
| 16 | Aucune inscription publique | 🟡 Moyen | Moyen |
| 17 | **AR1** — autorisation hors du métier | 🟡 Moyen | Élevé |
| 18 | Migrations irréversibles | 🟡 Moyen | Moyen |
| 19 | Pas de versioning d'API | 🟡 Moyen | Faible |
| 20 | PBKDF2 plutôt qu'Argon2 | 🟢 Faible | Faible |

---

## Feuille de route

**Court terme — avant tout utilisateur réel**
`S1` (15 min) · `D1` sauvegardes · `A2` workers · `Q1` couverture · finir le pipeline

**Moyen terme — avant d'ouvrir largement**
`A1` **chaîne par bar** — le chantier structurant · `S2` débit + Redis · `S4` pagination *(rupture de contrat : à faire avant qu'un client existe)* · `P1` N+1 · `S3` expiration des jetons · alertes

**Long terme — pour monter en charge**
Réplicas de lecture · journal en file d'attente · partitionnement par bar · `AR1` autorisation dans le métier · Argon2 · versioning d'API

---

## Ce qu'il faut préserver

Ces décisions sont **meilleures que la moyenne du secteur**. Les conserver telles quelles :

1. **Le journal inaltérable** — trigger PostgreSQL + chaînage SHA-256. Le cœur du produit, et il tient. *(Son partitionnement — A1 — ne remet pas en cause la propriété : il la rend tenable.)*
2. **Les contrats d'architecture exécutables** — `lint-imports` refuse ce qu'un document se contente de recommander.
3. **Le domaine pur** — vérifié, pas espéré.
4. **`mypy strict` sans exception** — 229 fichiers, zéro `ignore` de complaisance.
5. **Les tests qui prouvent le défaut avant de le corriger** — cloisonnement, capacités, idempotence : chacun a d'abord échoué en montrant le mal.
6. **Les garde-fous qui survivent à l'oubli** — le balayage des routes et l'inventaire du schéma ont attrapé `/api/sante/` sans que personne y pense.
7. **Les ADR qui écrivent ce qu'ils ne couvrent pas** — rare, et précieux.
8. **Le vocabulaire métier dans le code** — `Attribution`, `SousCaisse`, `EcartConstate`. Une gérante comprendrait les noms.

---

**Score global : 58 / 100** — *un socle sérieux, deux verrous à lever.*

Le code n'est pas le problème. **La topologie l'est.**
