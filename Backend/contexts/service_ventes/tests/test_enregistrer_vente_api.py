"""Test d'intégration : « Enregistrer une vente » de bout en bout."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import VenteModel
from contexts.service_ventes.tests.conftest import (
    inscrire_produit_via_api,
    ouvrir_service_via_api,
)
from shared.infrastructure.journal.models import MouvementModel

if TYPE_CHECKING:
    from django.contrib.auth.models import User


@pytest.mark.django_db
def test_enregistrer_une_vente_cree_la_vente_et_journalise(
    client_api: APIClient,
    auteur: User,
) -> None:
    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=650)

    reponse = client_api.post(
        f"/api/services/{service_id}/ventes/",
        {
            "produit_id": produit_id,
            "quantite": 3,
            "forme_paiement": "especes",
        },
        format="json",
    )

    assert reponse.status_code == 201
    corps = reponse.json()
    assert corps["montant_total"] == 1_950
    assert corps["service_id"] == service_id

    assert VenteModel.objects.count() == 1
    mouvement = MouvementModel.objects.get(type="VenteEnregistree")
    # La vente est attribuée à l'auteur authentifié, jamais à un id déclaré.
    assert mouvement.auteur_id == str(auteur.pk)


@pytest.mark.django_db
def test_une_vente_sur_un_service_inexistant_retourne_404(client_api: APIClient) -> None:
    produit_id = inscrire_produit_via_api(client_api, prix=650)

    reponse = client_api.post(
        "/api/services/inconnu/ventes/",
        {
            "produit_id": produit_id,
            "quantite": 1,
            "forme_paiement": "especes",
        },
        format="json",
    )

    assert reponse.status_code == 404
