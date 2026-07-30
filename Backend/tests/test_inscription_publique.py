"""Inscription publique — créer un compte et un premier bar."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_inscrire_un_nouvel_utilisateur() -> None:
    """S'inscrire crée un utilisateur, un bar et un compte avec capacités pleines."""
    client = APIClient()

    reponse = client.post(
        "/api/inscription/",
        {
            "username": "alice",
            "password": "motdepasse123",
            "email": "alice@example.com",
            "nom_bar": "Le Relais",
        },
        format="json",
    )

    assert reponse.status_code == 201
    data = reponse.json()
    assert data["user_id"] is not None
    assert data["bar_id"] is not None
    assert data["bar_nom"] == "Le Relais"
    assert "Inscription réussie" in data["message"]

    # L'utilisateur a été créé
    user = User.objects.get(username="alice")
    assert user.email == "alice@example.com"
    assert user.check_password("motdepasse123")


@pytest.mark.django_db
def test_inscrire_deux_fois_avec_le_meme_username_echoue() -> None:
    """Un username dupliqué est refusé."""
    client = APIClient()

    # Première inscription
    reponse1 = client.post(
        "/api/inscription/",
        {
            "username": "bob",
            "password": "motdepasse123",
            "nom_bar": "Mon Bar",
        },
        format="json",
    )
    assert reponse1.status_code == 201

    # Deuxième avec le même username
    reponse2 = client.post(
        "/api/inscription/",
        {
            "username": "bob",
            "password": "autremotdepasse",
            "nom_bar": "Autre Bar",
        },
        format="json",
    )

    assert reponse2.status_code == 409
    assert "existe déjà" in reponse2.json()["detail"]


@pytest.mark.django_db
def test_inscrire_sans_password_echoue() -> None:
    """Password est requis."""
    client = APIClient()

    reponse = client.post(
        "/api/inscription/",
        {
            "username": "charlie",
            "nom_bar": "Le Pub",
        },
        format="json",
    )

    assert reponse.status_code == 400
    assert "password" in str(reponse.content).lower()


@pytest.mark.django_db
def test_inscrire_sans_username_echoue() -> None:
    """Username est requis."""
    client = APIClient()

    reponse = client.post(
        "/api/inscription/",
        {
            "password": "motdepasse123",
            "nom_bar": "Le Pub",
        },
        format="json",
    )

    assert reponse.status_code == 400
    assert "username" in str(reponse.content).lower()


@pytest.mark.django_db
def test_utilisateur_inscrit_peut_obtenir_jeton() -> None:
    """Après inscription, l'utilisateur peut s'authentifier."""
    client = APIClient()

    # Inscription
    reponse_inscription = client.post(
        "/api/inscription/",
        {
            "username": "diane",
            "password": "motdepasse123",
            "nom_bar": "Chez Diane",
        },
        format="json",
    )
    assert reponse_inscription.status_code == 201

    # Obtenir jeton
    reponse_jeton = client.post(
        "/api/auth/jeton/",
        {
            "username": "diane",
            "password": "motdepasse123",
        },
        format="json",
    )

    assert reponse_jeton.status_code == 200
    assert "token" in reponse_jeton.json()


@pytest.mark.django_db
def test_email_optionnel() -> None:
    """L'email n'est pas obligatoire."""
    client = APIClient()

    reponse = client.post(
        "/api/inscription/",
        {
            "username": "eve",
            "password": "motdepasse123",
            "nom_bar": "Bar d'Eve",
        },
        format="json",
    )

    assert reponse.status_code == 201
    user = User.objects.get(username="eve")
    assert user.email == ""
