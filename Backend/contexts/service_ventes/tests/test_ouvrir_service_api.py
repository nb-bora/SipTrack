"""Test d'intégration : la tranche verticale « Ouvrir un service » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    MouvementModel,
    ServiceModel,
)


@pytest.mark.django_db
def test_ouvrir_service_cree_le_service_et_journalise_le_mouvement() -> None:
    client = APIClient()

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
    corps = reponse.json()
    assert corps["statut"] == "ouvert"
    assert corps["fond_de_caisse"] == 10_000

    assert ServiceModel.objects.count() == 1
    assert MouvementModel.objects.filter(type="ServiceOuvert").count() == 1


@pytest.mark.django_db
def test_lire_un_service_inexistant_retourne_404() -> None:
    client = APIClient()

    reponse = client.get("/api/services/inexistant/")

    assert reponse.status_code == 404
