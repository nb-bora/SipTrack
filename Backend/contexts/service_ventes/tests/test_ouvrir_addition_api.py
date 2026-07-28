"""Test d'intégration : « Ouvrir une addition » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import AdditionModel
from contexts.service_ventes.tests.conftest import ouvrir_service_via_api
from shared.infrastructure.journal.models import MouvementModel


@pytest.mark.django_db
def test_ouvrir_addition_cree_l_addition_et_journalise(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    reponse = client_api.post(
        f"/api/services/{service_id}/additions/",
        {"table_numero": 5},
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
def test_ouvrir_addition_sur_un_service_inexistant_retourne_404(client_api: APIClient) -> None:
    reponse = client_api.post(
        "/api/services/inexistant/additions/",
        {"table_numero": 5},
        format="json",
    )

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_ouvrir_addition_sur_un_service_non_ouvert_retourne_409(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    client_api.post(f"/api/services/{service_id}/cloture/", format="json")

    reponse = client_api.post(
        f"/api/services/{service_id}/additions/",
        {"table_numero": 5},
        format="json",
    )

    assert reponse.status_code == 409
