"""Test d'intégration : personne n'écrit dans le journal sans être authentifié."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from contexts.service_ventes.infrastructure.django_app.models import (
    MouvementModel,
    ServiceModel,
)
from shared.interface.rest.attribution import auteur_id_de

if TYPE_CHECKING:
    from django.contrib.auth.models import User

_OUVERTURE_SERVICE = {
    "bar_id": "bar1",
    "capacite": "operatrice",
    "fond_de_caisse": 10_000,
}


@pytest.mark.django_db
def test_ecrire_sans_jeton_est_refuse_et_ne_laisse_aucune_trace() -> None:
    client = APIClient()

    reponse = client.post("/api/services/", _OUVERTURE_SERVICE, format="json")

    assert reponse.status_code == 401
    assert ServiceModel.objects.count() == 0
    assert MouvementModel.objects.count() == 0


@pytest.mark.django_db
def test_lire_sans_jeton_est_refuse() -> None:
    client = APIClient()

    reponse = client.get("/api/services/peu-importe/")

    assert reponse.status_code == 401


@pytest.mark.django_db
def test_un_jeton_invalide_est_refuse() -> None:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token jeton-fabrique-de-toutes-pieces")

    reponse = client.post("/api/services/", _OUVERTURE_SERVICE, format="json")

    assert reponse.status_code == 401
    assert MouvementModel.objects.count() == 0


@pytest.mark.django_db
def test_obtenir_un_jeton_avec_de_bons_identifiants(
    auteur_identifie: User,
    mot_de_passe: str,
) -> None:
    client = APIClient()

    reponse = client.post(
        "/api/auth/jeton/",
        {"username": auteur_identifie.username, "password": mot_de_passe},
        format="json",
    )

    assert reponse.status_code == 200
    assert reponse.json()["token"]


@pytest.mark.django_db
def test_obtenir_un_jeton_avec_un_mauvais_mot_de_passe_est_refuse(
    auteur_identifie: User,
) -> None:
    client = APIClient()

    reponse = client.post(
        "/api/auth/jeton/",
        {"username": auteur_identifie.username, "password": "mauvais"},
        format="json",
    )

    assert reponse.status_code == 400
    assert "token" not in reponse.json()


@pytest.mark.django_db
def test_le_jeton_obtenu_ouvre_l_acces_et_attribue_le_fait(
    auteur_identifie: User,
    mot_de_passe: str,
) -> None:
    """Le parcours réel : j'obtiens un jeton, j'écris, le journal porte mon identité."""
    client = APIClient()
    reponse_jeton = client.post(
        "/api/auth/jeton/",
        {"username": auteur_identifie.username, "password": mot_de_passe},
        format="json",
    )
    assert reponse_jeton.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Token {reponse_jeton.json()['token']}")

    reponse = client.post("/api/services/", _OUVERTURE_SERVICE, format="json")

    assert reponse.status_code == 201
    mouvement = MouvementModel.objects.get(type="ServiceOuvert")
    assert mouvement.auteur_id == str(auteur_identifie.pk)


@pytest.mark.django_db
def test_un_auteur_ne_peut_pas_signer_au_nom_d_un_autre(
    client_api: APIClient,
    auteur: User,
) -> None:
    """Le cœur de la tranche : un auteur_id déclaré est ignoré, pas honoré."""
    reponse = client_api.post(
        "/api/services/",
        {**_OUVERTURE_SERVICE, "auteur_id": "la-gerante"},
        format="json",
    )

    assert reponse.status_code == 201
    mouvement = MouvementModel.objects.get(type="ServiceOuvert")
    assert mouvement.auteur_id == str(auteur.pk)
    assert mouvement.auteur_id != "la-gerante"


def test_une_requete_anonyme_ne_peut_pas_produire_d_auteur() -> None:
    """Filet sous `IsAuthenticated` : refuser d'écrire plutôt que mal attribuer.

    Si une vue oubliait la permission, `request.user.pk` vaudrait `None` et le
    journal enregistrerait un fait attribué à « None ».
    """
    from django.contrib.auth.models import AnonymousUser

    requete = Request(APIRequestFactory().post("/"))
    requete.user = AnonymousUser()

    with pytest.raises(NotAuthenticated):
        auteur_id_de(requete)
