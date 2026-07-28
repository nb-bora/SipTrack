"""Test d'intégration : la tranche verticale « Ouvrir un service » de bout en bout."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    MouvementModel,
    ServiceModel,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import User


@pytest.mark.django_db
def test_ouvrir_service_cree_le_service_et_journalise_le_mouvement(
    client_api: APIClient,
    auteur: User,
) -> None:
    reponse = client_api.post(
        "/api/services/",
        {
            "bar_id": "bar1",
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
    mouvement = MouvementModel.objects.get(type="ServiceOuvert")
    # Le fait est attribué à l'auteur authentifié, jamais à un id déclaré.
    assert mouvement.auteur_id == str(auteur.pk)


@pytest.mark.django_db
def test_lire_un_service_inexistant_retourne_404(client_api: APIClient) -> None:
    reponse = client_api.get("/api/services/inexistant/")

    assert reponse.status_code == 404
