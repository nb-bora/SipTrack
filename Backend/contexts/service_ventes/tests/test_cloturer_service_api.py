"""Test d'intégration : « Clôturer un service » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import ServiceModel
from contexts.service_ventes.tests.conftest import (
    ouvrir_addition_via_api,
    ouvrir_service_via_api,
)
from shared.infrastructure.journal.models import MouvementModel


@pytest.mark.django_db
def test_cloturer_service_met_le_statut_a_cloture_et_journalise(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    reponse = client_api.post(f"/api/services/{service_id}/cloture/", format="json")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["statut"] == "cloture"
    assert corps["clos_le"] is not None

    service_en_db = ServiceModel.objects.get(pk=service_id)
    assert service_en_db.statut == "cloture"
    assert service_en_db.clos_le is not None
    assert MouvementModel.objects.filter(type="ServiceCloture").count() == 1


@pytest.mark.django_db
def test_cloturer_un_service_inexistant_retourne_404(client_api: APIClient) -> None:
    reponse = client_api.post("/api/services/inexistant/cloture/", format="json")

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_cloturer_un_service_deja_cloture_retourne_409(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    # Première clôture : succès
    reponse1 = client_api.post(f"/api/services/{service_id}/cloture/", format="json")
    assert reponse1.status_code == 200

    # Deuxième clôture : conflit
    reponse2 = client_api.post(f"/api/services/{service_id}/cloture/", format="json")

    assert reponse2.status_code == 409


@pytest.mark.django_db
def test_cloturer_avec_une_addition_ouverte_retourne_409(client_api: APIClient) -> None:
    """Sans ce garde-fou, des consommations servies disparaissent du décompte."""
    service_id = ouvrir_service_via_api(client_api)
    ouvrir_addition_via_api(client_api, service_id)

    reponse = client_api.post(f"/api/services/{service_id}/cloture/", format="json")

    assert reponse.status_code == 409
    assert "1 addition(s) encore ouverte(s)" in reponse.json()["detail"]
    assert ServiceModel.objects.get(pk=service_id).statut == "ouvert"
    assert MouvementModel.objects.filter(type="ServiceCloture").count() == 0


@pytest.mark.django_db
def test_cloturer_apres_reglement_de_toutes_les_additions_reussit(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    reponse = client_api.post(f"/api/services/{service_id}/cloture/", format="json")

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "cloture"
