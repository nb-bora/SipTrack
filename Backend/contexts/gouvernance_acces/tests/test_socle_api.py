"""Test d'intégratio du socle Gouvernance : Bar + Compte + Capacités."""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_creer_un_bar(client_api: APIClient, auteur: Any) -> None:
    """Créer un bar appartenant à l'utilisateur authentifié."""
    reponse = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json")

    assert reponse.status_code == 201
    assert reponse.json()["nom"] == "Le Relais"
    assert reponse.json()["proprietaire_id"] == str(auteur.pk)


@pytest.mark.django_db
def test_lister_mes_bars(client_api: APIClient, auteur: Any) -> None:
    """Lister tous les bars que je possède."""
    client_api.post("/api/bars/", {"nom": "Bar 1"}, format="json")
    client_api.post("/api/bars/", {"nom": "Bar 2"}, format="json")

    reponse = client_api.get("/api/bars/", format="json")

    assert reponse.status_code == 200
    # On vérifie la présence plutôt qu'un décompte : l'auteur possède aussi le
    # bar où se déroulent les scénarios, et compter le total ferait échouer ce
    # test pour une raison sans rapport avec ce qu'il éprouve.
    noms = {bar["nom"] for bar in reponse.json()}
    assert {"Bar 1", "Bar 2"} <= noms


@pytest.mark.django_db
def test_deux_bars_meme_nom_refuses(client_api: APIClient) -> None:
    """Créer deux bars avec le même nom est refusé."""
    client_api.post("/api/bars/", {"nom": "Doublon"}, format="json")

    reponse = client_api.post("/api/bars/", {"nom": "Doublon"}, format="json")

    assert reponse.status_code == 409


@pytest.mark.django_db
def test_creer_un_compte_dans_un_bar(
    client_api: APIClient, auteur: Any, django_user_model: Any
) -> None:
    """Créer un compte utilisateur dans un bar."""
    # Créer le bar (automatiquement crée un compte pour le propriétaire).
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    # Créer un autre utilisateur.
    autre = django_user_model.objects.create_user(username="alice", password="secret")

    # Créer un compte pour cet utilisateur avec des capacités initiales.
    # Cela marche car le propriétaire du bar (auteur) a TOUTES les capacités.
    reponse = client_api.post(
        "/api/comptes/",
        {
            "bar_id": bar["id"],
            "user_id": str(autre.pk),
            "capacites_initiales": ["encaisser"],
        },
        format="json",
    )

    assert reponse.status_code == 201
    assert reponse.json()["user_id"] == str(autre.pk)
    assert "encaisser" in reponse.json()["capacites"]


@pytest.mark.django_db
def test_accorder_une_capacite(client_api: APIClient, auteur: Any, django_user_model: Any) -> None:
    """Accorder une capacité à un compte."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    autre = django_user_model.objects.create_user(username="alice", password="secret")

    compte = client_api.post(
        "/api/comptes/",
        {"bar_id": bar["id"], "user_id": str(autre.pk), "capacites_initiales": []},
        format="json",
    ).json()

    # Accorder une capacité.
    reponse = client_api.post(
        f"/api/comptes/{compte['id']}/capacites/",
        {"capacite": "encaisser"},
        format="json",
    )

    assert reponse.status_code == 200
    assert "encaisser" in reponse.json()["capacites"]


@pytest.mark.django_db
def test_idempotence_creer_bar(client_api: APIClient) -> None:
    """Créer le même bar deux fois : 201 puis 409."""
    payload = {"nom": "Le Relais"}

    reponse1 = client_api.post("/api/bars/", payload, format="json")
    assert reponse1.status_code == 201

    reponse2 = client_api.post("/api/bars/", payload, format="json")
    assert reponse2.status_code == 409


@pytest.mark.django_db
def test_idempotence_creer_compte(client_api: APIClient, django_user_model: Any) -> None:
    """Créer le même compte deux fois : 201 puis 409."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()
    autre = django_user_model.objects.create_user(username="alice", password="secret")

    payload = {
        "bar_id": bar["id"],
        "user_id": str(autre.pk),
        "capacites_initiales": [],
    }

    reponse1 = client_api.post("/api/comptes/", payload, format="json")
    assert reponse1.status_code == 201

    reponse2 = client_api.post("/api/comptes/", payload, format="json")
    assert reponse2.status_code == 409
