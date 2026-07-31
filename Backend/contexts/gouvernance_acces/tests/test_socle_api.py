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


def _rattacher(user: Any, bar_id: str, capacites: list[str]) -> None:
    """Donne un compte à `user` dans `bar_id`, sans passer par l'API.

    L'API exige déjà une capacité pour créer un compte ; ce raccourci pose la
    situation à éprouver — quelqu'un travaille ici — sans faire dépendre le test
    de la route qui l'établit.
    """
    from contexts.gouvernance_acces.infrastructure.django_app.models import (
        BarModel,
        CompteModel,
    )

    CompteModel.objects.create(
        id=f"compte-{user.pk}-{bar_id}",
        bar=BarModel.objects.get(id=bar_id),
        user=user,
        capacites=capacites,
    )


def _client_de(user: Any) -> APIClient:
    """Un client REST authentifié au nom de `user`."""
    from rest_framework.authtoken.models import Token

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
    return client


@pytest.mark.django_db
def test_lister_expose_les_bars_ou_l_on_travaille_sans_les_posseder(
    bar_de_test: str, django_user_model: Any
) -> None:
    """Une employée voit le bar où elle tient un compte.

    C'est la porte d'entrée de l'application : sans ce bar dans sa liste, elle
    ne peut en sélectionner aucun, et tous les autres écrans lui restent fermés.
    """
    employee = django_user_model.objects.create_user(username="awa")
    _rattacher(employee, bar_de_test, ["enregistrer_vente"])

    reponse = _client_de(employee).get("/api/bars/", format="json")

    assert reponse.status_code == 200
    assert [bar["id"] for bar in reponse.json()] == [bar_de_test]


@pytest.mark.django_db
def test_lister_ne_montre_rien_a_qui_n_a_de_compte_nulle_part(
    bar_de_test: str, django_user_model: Any
) -> None:
    """Une liste vide, pas une erreur — et surtout aucun bar d'autrui."""
    etrangere = django_user_model.objects.create_user(username="inconnue")

    reponse = _client_de(etrangere).get("/api/bars/", format="json")

    assert reponse.status_code == 200
    assert reponse.json() == []


@pytest.mark.django_db
def test_lister_ne_repete_pas_le_bar_dont_on_est_aussi_proprietaire(
    client_api: APIClient, bar_de_test: str
) -> None:
    """Le propriétaire tient également un compte chez lui : le bar sort une fois.

    Sans `distinct()`, la jointure sur les comptes le ramènerait deux fois — et
    l'application afficherait deux entrées pour un seul établissement.
    """
    reponse = client_api.get("/api/bars/", format="json")

    assert reponse.status_code == 200
    identifiants = [bar["id"] for bar in reponse.json()]
    assert identifiants.count(bar_de_test) == 1


@pytest.mark.django_db
def test_lister_reste_cloisonne_entre_bars(
    client_api: APIClient, bar_de_test: str, django_user_model: Any
) -> None:
    """Le bar d'une tierce personne ne fuit pas dans ma liste."""
    tierce = django_user_model.objects.create_user(username="tierce")
    _client_de(tierce).post("/api/bars/", {"nom": "Chez la voisine"}, format="json")

    reponse = client_api.get("/api/bars/", format="json")

    assert reponse.status_code == 200
    assert "Chez la voisine" not in {bar["nom"] for bar in reponse.json()}


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
def test_creer_un_compte_avec_user_id_introuvable(client_api: APIClient) -> None:
    """Créer un compte avec un user_id qui n'existe pas → 404."""
    # Créer un bar.
    bar = client_api.post("/api/bars/", {"nom": "Le Bar"}, format="json").json()

    # Tenter de créer un compte avec un user_id bidon.
    reponse = client_api.post(
        "/api/comptes/",
        {
            "bar_id": bar["id"],
            "user_id": "999999",  # n'existe pas
            "capacites_initiales": [],
        },
        format="json",
    )

    assert reponse.status_code == 404
    assert "Utilisateur introuvable" in reponse.json()["detail"]


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
