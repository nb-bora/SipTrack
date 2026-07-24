"""Test d'intégration : « Enregistrer une vente » de bout en bout."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    MouvementModel,
    VenteModel,
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
def test_enregistrer_une_vente_cree_la_vente_et_journalise() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    reponse = client.post(
        f"/api/services/{service_id}/ventes/",
        {
            "auteur_id": "u1",
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
def test_une_vente_sur_un_service_inexistant_retourne_404() -> None:
    client = APIClient()

    reponse = client.post(
        "/api/services/inconnu/ventes/",
        {
            "auteur_id": "u1",
            "produit_id": "33export",
            "quantite": 1,
            "prix_unitaire": 650,
            "forme_paiement": "especes",
        },
        format="json",
    )

    assert reponse.status_code == 404
