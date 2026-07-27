"""Test d'intégration : « Régler une addition » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    AdditionModel,
    MouvementModel,
    ServiceModel,
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
    return reponse.json()["id"]


def _ouvrir_addition(client: APIClient, service_id: str) -> str:
    reponse = client.post(
        f"/api/services/{service_id}/additions/",
        {"auteur_id": "u1", "table_numero": 5},
        format="json",
    )
    assert reponse.status_code == 201
    return reponse.json()["id"]


@pytest.mark.django_db
def test_regler_une_addition_cree_un_mouvement_et_retourne_200() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    reponse = client.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        {"auteur_id": "u1"},
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
def test_regler_une_addition_introuvable_retourne_404() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    reponse = client.post(
        f"/api/services/{service_id}/additions/add-inexistante/reglement/",
        {"auteur_id": "u1"},
        format="json",
    )

    assert reponse.status_code == 404
    assert "introuvable" in reponse.json()["detail"].lower()


@pytest.mark.django_db
def test_regler_une_addition_deja_reglee_retourne_409() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    AdditionModel.objects.filter(pk=addition_id).update(
        statut="reglee",
        ferme_le="2026-07-28T22:30:00Z",
    )

    reponse = client.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        {"auteur_id": "u1"},
        format="json",
    )

    assert reponse.status_code == 409
    assert "déjà" in reponse.json()["detail"].lower()
