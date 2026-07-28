"""Test d'intégration : « Régler une addition » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    AdditionModel,
    MouvementModel,
)
from contexts.service_ventes.tests.conftest import (
    ouvrir_addition_via_api,
    ouvrir_service_via_api,
)


@pytest.mark.django_db
def test_regler_une_addition_cree_un_mouvement_et_retourne_200(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["statut"] == "reglee"
    assert corps["ferme_le"] is not None

    addition_en_db = AdditionModel.objects.get(pk=addition_id)
    assert addition_en_db.statut == "reglee"
    assert addition_en_db.ferme_le is not None
    assert MouvementModel.objects.filter(type="AdditionReglee").count() == 1


@pytest.mark.django_db
def test_regler_une_addition_introuvable_retourne_404(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    reponse = client_api.post(
        f"/api/services/{service_id}/additions/add-inexistante/reglement/",
        format="json",
    )

    assert reponse.status_code == 404
    assert "introuvable" in reponse.json()["detail"].lower()


@pytest.mark.django_db
def test_regler_une_addition_deja_reglee_retourne_409(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    AdditionModel.objects.filter(pk=addition_id).update(
        statut="reglee",
        ferme_le="2026-07-28T22:30:00Z",
    )

    reponse = client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    assert reponse.status_code == 409
    assert "clôturée" in reponse.json()["detail"].lower()


@pytest.mark.django_db
def test_regler_une_addition_avec_mauvais_service_id_retourne_404(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    other_service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = client_api.post(
        f"/api/services/{other_service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    assert reponse.status_code == 404
    assert "introuvable" in reponse.json()["detail"].lower()
