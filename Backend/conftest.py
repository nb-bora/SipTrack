"""Fixtures partagées par tous les bounded contexts.

L'authentification n'appartient à aucun contexte en particulier : tout test qui
écrit un Fait a besoin d'un auteur authentifié.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient

if TYPE_CHECKING:
    from django.contrib.auth.models import User

# Mot de passe de test uniquement — aucun compte réel n'utilise cette valeur.
MOT_DE_PASSE_TEST = "mot-de-passe-de-test"  # noqa: S105


@pytest.fixture
def mot_de_passe() -> str:
    return MOT_DE_PASSE_TEST


@pytest.fixture
def auteur(db: None) -> User:
    """Un acteur authentifiable, répondant des faits qu'il écrit.

    Sans mot de passe : l'accès par jeton n'en a pas besoin, et hacher un mot de
    passe (PBKDF2, volontairement lent) dans chaque test coûtait dix fois le
    temps de la suite. Voir `auteur_identifie` pour les tests de connexion.
    """
    from django.contrib.auth.models import User

    return User.objects.create_user(username="serveuse1")


@pytest.fixture
def auteur_identifie(auteur: User) -> User:
    """Un acteur qui peut se connecter par identifiant / mot de passe."""
    auteur.set_password(MOT_DE_PASSE_TEST)
    auteur.save()
    return auteur


@pytest.fixture
def client_api(auteur: User) -> APIClient:
    """Client REST authentifié par jeton, comme le sera l'app mobile."""
    from rest_framework.authtoken.models import Token

    jeton = Token.objects.create(user=auteur)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {jeton.key}")
    return client
