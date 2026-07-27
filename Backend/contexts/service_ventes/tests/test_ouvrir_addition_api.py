"""Test d'intégration : « Ouvrir une addition » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    AdditionModel,
    MouvementModel,
)


def _ouvrir_service(client: APIClient) -> str:
    reponse = client.post(
        "/api/services/",
        {
            "bar_id": "bar1",
            "auteur_id": "u1",
            "capacite": "operatrice",
            "fond_de_caisse": 10_000,
        },
        format="json",
    )
    assert reponse.status_code == 201
    service_id: str = reponse.json()["id"]
    return service_id


@pytest.mark.django_db
def test_ouvrir_addition_cree_l_addition_et_journalise() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    reponse = client.post(
        f"/api/services/{service_id}/additions/",
        {
            "auteur_id": "u1",
            "table_numero": 5,
        },
        format="json",
    )

    assert reponse.status_code == 201
    corps = reponse.json()
    assert corps["statut"] == "ouverte"
    assert corps["table_numero"] == 5

    addition_en_db = AdditionModel.objects.get(pk=corps["id"])
    assert addition_en_db.statut == "ouverte"
    assert addition_en_db.table_numero == 5
    assert MouvementModel.objects.filter(type="AdditionOuverte").count() == 1


@pytest.mark.django_db
def test_ouvrir_addition_sur_un_service_inexistant_retourne_404() -> None:
    client = APIClient()

    reponse = client.post(
        "/api/services/inexistant/additions/",
        {
            "auteur_id": "u1",
            "table_numero": 5,
        },
        format="json",
    )

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_ouvrir_addition_sur_un_service_non_ouvert_retourne_409() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    # Clôturer le service
    client.post(f"/api/services/{service_id}/cloture/", {"auteur_id": "u1"}, format="json")

    # Essayer d'ouvrir une addition
    reponse = client.post(
        f"/api/services/{service_id}/additions/",
        {
            "auteur_id": "u1",
            "table_numero": 5,
        },
        format="json",
    )

    assert reponse.status_code == 409
