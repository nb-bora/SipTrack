"""Test d'intégration : « Enregistrer une vente » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    MouvementModel,
    VenteModel,
)
from contexts.service_ventes.tests.conftest import ouvrir_service_via_api


@pytest.mark.django_db
def test_enregistrer_une_vente_cree_la_vente_et_journalise(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    reponse = client_api.post(
        f"/api/services/{service_id}/ventes/",
        {
            "produit_id": "33export",
            "quantite": 3,
            "prix_unitaire": 650,
            "forme_paiement": "especes",
        },
        format="json",
    )

    assert reponse.status_code == 201
    corps = reponse.json()
    assert corps["montant_total"] == 1_950
    assert corps["service_id"] == service_id

    assert VenteModel.objects.count() == 1
    assert MouvementModel.objects.filter(type="VenteEnregistree").count() == 1


@pytest.mark.django_db
def test_une_vente_sur_un_service_inexistant_retourne_404(client_api: APIClient) -> None:
    reponse = client_api.post(
        "/api/services/inconnu/ventes/",
        {
            "produit_id": "33export",
            "quantite": 1,
            "prix_unitaire": 650,
            "forme_paiement": "especes",
        },
        format="json",
    )

    assert reponse.status_code == 404
