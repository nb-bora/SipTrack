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


# Identifiant du bar où travaillent les tests. Les scénarios le passent en dur
# depuis toujours ; il désigne désormais un bar réellement existant, puisque agir
# quelque part suppose d'y tenir un compte.
BAR_DE_TEST = "bar1"


@pytest.fixture
def bar_de_test(auteur: User) -> str:
    """Un bar où `auteur` tient un compte, avec toutes les capacités.

    Créé directement en base plutôt que par l'API : passer par `POST /api/bars/`
    donnerait un identifiant tiré au hasard, alors que les scénarios existants
    nomment ce bar « bar1 ». Le contenu est identique à ce que produit le cas
    d'usage — un bar, et un compte de propriétaire qui peut tout y faire.

    Les tests d'autorisation, eux, passent par l'API : c'est le chemin qu'ils
    éprouvent.
    """
    from contexts.gouvernance_acces.domain.enums import CapaciteAtomique
    from contexts.gouvernance_acces.infrastructure.django_app.models import (
        BarModel,
        CompteModel,
    )

    bar = BarModel.objects.create(id=BAR_DE_TEST, nom="Bar de test", proprietaire=auteur)
    CompteModel.objects.create(
        id=f"compte-{auteur.pk}-{BAR_DE_TEST}",
        bar=bar,
        user=auteur,
        capacites=sorted(CapaciteAtomique.toutes()),
    )
    return BAR_DE_TEST


@pytest.fixture
def autre_bar_de_test(auteur: User, bar_de_test: str) -> str:
    """Un second bar, appartenant au **même** auteur.

    Sert aux scénarios qui opposent deux bars sans mettre en jeu l'autorisation :
    qu'une même personne tienne deux établissements est courant, et le catalogue
    de l'un ne doit pas fixer les prix de l'autre pour autant.
    """
    from contexts.gouvernance_acces.domain.enums import CapaciteAtomique
    from contexts.gouvernance_acces.infrastructure.django_app.models import (
        BarModel,
        CompteModel,
    )

    bar = BarModel.objects.create(id="bar2", nom="Second bar de test", proprietaire=auteur)
    CompteModel.objects.create(
        id=f"compte-{auteur.pk}-bar2",
        bar=bar,
        user=auteur,
        capacites=sorted(CapaciteAtomique.toutes()),
    )
    return "bar2"


@pytest.fixture
def client_api(auteur: User, bar_de_test: str) -> APIClient:
    """Client REST authentifié par jeton, comme le sera l'app mobile.

    Dépend de `bar_de_test` : un client authentifié qui n'a de compte nulle part
    ne peut plus rien faire, et tous les scénarios travaillent dans ce bar.
    """
    from rest_framework.authtoken.models import Token

    jeton = Token.objects.create(user=auteur)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {jeton.key}")
    return client
