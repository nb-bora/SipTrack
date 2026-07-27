"""Test d'intégration : « Clôturer un service » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
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
    service_id: str = reponse.json()["id"]
    return service_id


@pytest.mark.django_db
def test_cloturer_service_met_le_statut_a_cloture_et_journalise() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    reponse = client.post(
        f"/api/services/{service_id}/cloture/",
        {"auteur_id": "u1"},
        format="json",
    )

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["statut"] == "cloture"
    assert corps["clos_le"] is not None

    service_en_db = ServiceModel.objects.get(pk=service_id)
    assert service_en_db.statut == "cloture"
    assert service_en_db.clos_le is not None
    assert MouvementModel.objects.filter(type="ServiceCloture").count() == 1


@pytest.mark.django_db
def test_cloturer_un_service_inexistant_retourne_404() -> None:
    client = APIClient()

    reponse = client.post(
        "/api/services/inexistant/cloture/",
        {"auteur_id": "u1"},
        format="json",
    )

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_cloturer_un_service_deja_cloture_retourne_409() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    # Première clôture : succès
    reponse1 = client.post(
        f"/api/services/{service_id}/cloture/",
        {"auteur_id": "u1"},
        format="json",
    )
    assert reponse1.status_code == 200

    # Deuxième clôture : conflit
    reponse2 = client.post(
        f"/api/services/{service_id}/cloture/",
        {"auteur_id": "u1"},
        format="json",
    )

    assert reponse2.status_code == 409
