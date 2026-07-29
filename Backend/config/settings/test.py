"""Réglages de la suite de tests.

Identiques au développement, à une exception : le hachage des mots de passe.

Argon2id est **lent à dessein** — c'est ce qui le rend bon en production. Dans
une suite qui crée des comptes par dizaines, ce coût multipliait la durée totale
par quatre sans rien éprouver de plus. Le hachage lui-même est vérifié
séparément, en réactivant explicitement la configuration de production.
"""

from .dev import *  # noqa: F403  # NOSONAR

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
