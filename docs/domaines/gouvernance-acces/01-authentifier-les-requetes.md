# Fonctionnalité : Authentifier les requêtes et attribuer les faits

## Vue d'ensemble

**Domaine** : Gouvernance & Accès  
**Acteur** : Toute personne qui écrit dans le journal  
**Déclencheur** : Chaque appel à l'API  
**Résultat** : Aucun Fait n'est écrit sans auteur authentifié

## Le problème que ça règle

Jusqu'ici `auteur_id` arrivait **dans le corps de la requête**. Le journal enregistrait
donc consciencieusement des attributions que personne ne vérifiait : n'importe qui
pouvait écrire une vente au nom de n'importe quelle serveuse. L'invariant 2 du modèle
métier — « aucun Fait sans attribution, personne au-dessus du journal » — était
formellement respecté et matériellement vide.

## Ce qui change

| Avant | Après |
|---|---|
| `auteur_id` dans le corps de la requête | Déduit du compte authentifié |
| Aucune authentification | Jeton obligatoire sur **toutes** les routes |
| Aucune route protégée par défaut | Fermé par défaut (`IsAuthenticated` global) |

## Contrats API

### Obtenir un jeton — `POST /api/auth/jeton/`

```json
{ "username": "serveuse1", "password": "..." }
```
→ `200 { "token": "9c8f..." }` · `400` si identifiants invalides

Seule route ouverte du système, donc la seule exposée au bourrinage : elle est
limitée en débit (`THROTTLE_OBTENTION_JETON`, 10/min par défaut).

### Toutes les autres routes

En-tête obligatoire : `Authorization: Token 9c8f...` — sinon `401`.

## Décisions de conception

### Jeton plutôt que session ou JWT

L'app mobile est **offline-first** : elle ne peut dépendre ni d'une session serveur, ni
d'un cycle de rafraîchissement qui expire pendant un service sans réseau. Un jeton
sans expiration, révocable en supprimant sa ligne, correspond à l'usage réel : 2-3 bars,
comptes créés à la main.

### `auteur_id` = clé technique, jamais le nom

On journalise `str(user.pk)`. Renommer un compte ne doit pas réécrire l'histoire déjà
écrite — un journal dont les entrées changent de sens après coup ne prouve rien.

### La capacité reste déclarée par acte

`capacite` reste dans le corps de la requête, et **ce n'est pas une faiblesse** : le
modèle métier (§3) pose que l'attribution se fait « par acte et par capacité, jamais par
rôle figé » — la gérante peut être opératrice un jour, superviseuse le lendemain. C'est
l'**identité** qui doit être prouvée, pas la capacité, qui est un choix assumé au moment
de l'acte et journalisé comme tel.

### Fermé par défaut

`IsAuthenticated` est posé globalement, pas vue par vue. Une route ajoutée demain est
protégée sans que personne ait à y penser ; l'inverse (ouvrir par défaut, penser à
fermer) produit tôt ou tard une route oubliée.

## Ce que ça ne couvre pas

L'authentification prouve **qui** écrit, pas **ce que cette personne a le droit de
faire**. Tout compte authentifié peut aujourd'hui tout faire : les régimes de décision
(réservé / sous politique / pleinement délégué) restent à implémenter, de même qu'un
véritable agrégat `Acteur` en remplacement de l'utilisateur Django.

Limite assumée, sans danger tant que les comptes sont créés à la main pour un usage
interne — bloquante dès qu'un compte est confié à quelqu'un dont on ne veut pas qu'il
puisse tout faire.

## Chemins de test

- `contexts/gouvernance_acces/tests/test_authentification_api.py` :
  - écriture sans jeton → 401 **et aucune trace en base**
  - jeton fabriqué → 401
  - obtention d'un jeton, bon et mauvais mot de passe
  - parcours réel : jeton obtenu → écriture → le journal porte l'identité réelle
  - **un `auteur_id` déclaré dans le corps est ignoré, pas honoré**

## Composition verticale

| Couche | Fichiers |
|---|---|
| **Interface** | `contexts/gouvernance_acces/interface/rest/views.py::ObtenirJetonView` |
| **Partagé** | `shared/interface/rest/attribution.py::auteur_id_de()` |
| **Configuration** | `config/settings/base.py` (REST_FRAMEWORK), `config/urls.py` |

---

**Statut** : ✅ LIVRÉ (branche `feat/authentification`, ticket #24)  
**Quality Gate** : Ruff ✓ + MyPy ✓ + lint-imports (5 contrats) ✓ + 85 tests ✓  
**Dernière mise à jour** : 2026-07-28
