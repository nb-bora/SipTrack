# ADR-0009 — Un rejeu ne crée qu'un seul fait

**Statut** : accepté — 2026-07-29
**Contexte** : ticket #55, dernier blocker de l'audit de sécurité

## Le problème

L'application mobile est offline-first. À la reconnexion, elle rejoue ce qui n'a
pas abouti — c'est le comportement **correct** d'un client hors ligne, pas un
défaut.

```
POST /api/services/{id}/ventes/   →  timeout réseau
le client rejoue                  →  la requête repart
                                  →  DEUX ventes pour UNE consommation
```

Le journal étant immuable, ce doublon ne se défait pas. Il gonfle la recette
attendue, et la réconciliation de fin de service accusera une serveuse qui n'a
rien fait.

**C'est ce qui distingue ce défaut des deux précédents** (ADR-0006) : ceux-là
protégeaient d'un acte malveillant. Celui-ci corrompt les données sans que
personne ne fasse rien de mal.

### Ce qui existait déjà ne suffisait pas

Le commit `397ca88` attrape les `IntegrityError` sur contraintes uniques : deux
créations simultanées du même bar ne passent pas deux fois. Cela couvre la
**concurrence sur des objets nommés**, pas le **rejeu d'un fait qui n'a aucune
raison d'être unique** — une serveuse peut légitimement saisir deux fois la même
bière au même prix.

Rien dans le contenu d'une requête ne dit si c'est un doublon. Seule une clé
fournie par le client le dit.

## La décision

En-tête `Idempotency-Key`, **obligatoire** sur les écritures authentifiées.

| Situation | Réponse |
|---|---|
| Clé inconnue | la requête s'exécute, la réponse est mémorisée |
| Clé déjà terminée | la réponse mémorisée, à l'identique, avec `Idempotency-Replayed: true` |
| Clé en cours | `409` — réessayez |
| Clé réutilisée, corps différent | `422` |
| Clé absente | `400` |

### Pourquoi obligatoire

La rendre facultative reviendrait à compter sur le fait qu'aucun client n'oublie
jamais de l'envoyer — or c'est précisément cet oubli qu'on couvre. Le nom de
l'en-tête suit l'usage établi (Stripe et consorts) : les développeurs mobiles le
reconnaîtront.

### L'unicité porte sur *(porteur, clé)*, pas sur la clé seule

Deux clients qui choisiraient la même valeur ne doivent ni se gêner, ni pouvoir
lire la réponse l'un de l'autre. Le porteur est une **empreinte du jeton** —
jamais le jeton lui-même.

### Un échec libère sa clé

Retenir un `500` condamnerait la vente pour de bon, alors que **rien n'a été
écrit** : l'Unit of Work a tout annulé. Le client doit pouvoir corriger et
rejouer.

### Un point de reprise autour de l'insertion

La violation d'unicité est le cas **normal** d'un rejeu, pas une anomalie. Sans
`transaction.atomic()`, elle condamnerait la transaction englobante et
interdirait la lecture qui suit immédiatement.

`ATOMIC_REQUESTS` vaut `False` : la trace s'écrit hors de la transaction du cas
d'usage, donc elle est visible des requêtes concurrentes. C'est ce qui rend la
garantie tenable.

## Ce qui a été écarté

**Déduire le doublon du contenu de la requête.** Deux ventes identiques à une
seconde d'intervalle sont indiscernables d'un rejeu — sauf pour le client, qui
sait s'il a rejoué. Une heuristique aurait fait disparaître des ventes réelles :
bien pire que le problème qu'elle résout.

**Exiger la clé même sans jeton.** Un appel non authentifié n'a rien à rejouer,
et c'est à l'authentification de répondre. Lui réclamer une clé avant de lui dire
qu'il n'est pas identifié inverserait l'ordre des refus.

## Une limite assumée

Un appel portant un jeton **invalide** mais aucune clé reçoit `400` avant `401` :
le middleware ne peut pas authentifier, l'authentification a lieu plus loin, dans
la vue. Aucune conséquence de sécurité — les deux réponses sont des refus — mais
l'ordre est contre-intuitif. Le corriger supposerait de déplacer l'idempotence
dans DRF plutôt qu'en middleware.

## Conséquences

- Tout client écrivant sur l'API doit envoyer une clé par opération. Le client de
  test en génère une neuve à chaque appel, et une clé explicite l'emporte : c'est
  ainsi que les tests de rejeu en envoient deux fois la même.
- Le volume est borné par comparaison à la plus grande clé primaire, jamais par
  `COUNT(*)`. `IDEMPOTENCE_CLES_MAX` vient de l'environnement.
- Une clé couvre un rejeu qui suit de près la requête d'origine : la mémoire n'a
  pas à être longue.
