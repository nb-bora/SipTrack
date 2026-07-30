# ADR-0010 — Clé de repli, débit, jetons, hachage

**Statut** : accepté — 2026-07-29
**Contexte** : constats S1–S3 et hachage de [l'audit technique](../08-audit-technique.md)

## S1 — La production refuse de démarrer sans `SECRET_KEY`

`base.py` porte une valeur de repli pour le développement. **Vérifié** : la
retirer de l'environnement laissait la production démarrer quand même, avec
cette valeur — publiée dans un dépôt public.

`config/settings/prod.py` lit désormais `SECRET_KEY` par `exiger()`, qui lève
`ConfigurationManquante` si la variable est absente ou vide. Une panne au
démarrage se voit dans les journaux Render ; une clé de repli qui sert
silencieusement ne se voit pas.

### Pourquoi le garde vit dans son propre module

Il était d'abord dans `prod.py`. La CI l'a rejeté, et à raison : `prod.py`
**appelle** le garde au chargement, donc l'importer pour l'éprouver le
déclenchait. Le test ne pouvait passer que dans un environnement déjà
configuré — c'est-à-dire jamais là où le garde sert. En local il passait, un
fichier `.env` fournissant la clé ; en CI, non.

`config/settings/garde.py` n'a aucun effet de bord : il s'importe, et se teste.
Un module qui en a se contente d'être exécuté.

## S2 — Débit limité sur l'ensemble de l'API

`ScopedRateThrottle` ne freinait que les vues déclarant un `throttle_scope` —
une seule le faisait. `UserRateThrottle` (300/min) et `AnonRateThrottle`
(30/min) couvrent maintenant tout le reste, `ScopedRateThrottle` restant pour
le cas particulier de l'obtention de jeton (10/min).

Le plafond utilisateur est volontairement large : une serveuse en coup de feu
saisit vite, et un plafond trop bas ferait contourner l'outil — plus coûteux
que l'abus qu'il prévient.

### Une limite de test qui vaut d'être connue

`override_settings(REST_FRAMEWORK=...)` **prend effet mais ne se restaure pas**
pour les classes de limitation de débit de DRF : `THROTTLE_RATES` est lu une
fois à l'instanciation et mis en cache sur la classe. Un test qui réduit le
débit temporairement le laisse réduit pour tous les tests suivants, et le
résultat dépend alors de l'ordre d'exécution — la pire sorte d'instabilité.

Les tests éprouvent donc le débit **tel qu'il est réellement configuré**, sans
le muter : le quota d'obtention de jeton (10/min, le plus bas) pour prouver le
freinage, le quota utilisateur (300/min) pour prouver l'absence de gêne.

`/api/sante/` est exemptée du freinage : Render la sonde en continu et la CI
l'interroge en boucle pour constater un déploiement (ADR précédent). La
soumettre au quota anonyme la ferait échouer précisément pendant un incident ou
un déploiement.

### Une limite de fond qui reste à lever

Les compteurs s'appuient sur le cache Django, `locmemcache` par défaut — donc
**par processus**. Juste avec un seul worker (cf. audit, A2), mais faux dès que
plusieurs workers tournent : chacun compterait séparément, et la limite réelle
serait `N × 300/min`. `CACHE_URL` bascule vers Redis en une variable
d'environnement, sans changement de code — c'est du provisionnement, pas du
développement, donc hors du périmètre de ce correctif.

## S3 — Jetons datés, et révocables

`JetonExpirable` (`shared/interface/rest/authentification.py`) étend
`TokenAuthentication` : au-delà de `JETON_DUREE_JOURS` (30 par défaut), le
jeton est **supprimé** et refusé. Supprimer plutôt que laisser dormir évite
qu'une table de jetons morts grossisse indéfiniment, et rend le refus
définitif — un jeton expiré ne redevient pas valide si l'horloge recule.

`POST /api/auth/deconnexion/` supprime le jeton présenté. Sans cet endpoint, la
seule façon de couper l'accès d'un téléphone volé aurait été d'intervenir en
base — ce qui n'est pas une révocation utilisable.

## Hachage des mots de passe : Argon2id

Remplace PBKDF2 (défaut Django), retenu par l'OWASP pour sa résistance au
cassage par GPU. PBKDF2 et consorts restent déclarés en second recours : les
comptes créés avant continuent de se connecter, et sont réencodés en Argon2 à
la prochaine connexion — Django le fait de lui-même.

### Argon2 est lent par conception, et c'est voulu — sauf en test

C'est ce qui le rend bon en production. Dans une suite qui crée des comptes par
dizaines, ce coût multipliait la durée totale par plus de deux (43 s contre
127 s mesurés). `config/settings/test.py` bascule sur un hachage rapide pour la
suite ; le test qui vérifie Argon2 réactive explicitement la configuration de
production plutôt que de dépendre de l'environnement d'exécution.

## Conséquences

- Tout déploiement sans `SECRET_KEY` échoue au démarrage — attendu, et
  documenté dans `docs/06-deploiement.md`.
- Les clients existants continuent de fonctionner jusqu'à l'expiration de leur
  jeton actuel ; le format du jeton lui-même n'a pas changé.
- `CACHE_URL=redis://...` est le prochain pas nécessaire dès qu'un second
  worker est provisionné (cf. ADR sur A2, à venir).
