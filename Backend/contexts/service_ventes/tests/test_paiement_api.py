"""Test d'intégration : « Paiement partiel » de bout en bout."""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import (
    AdditionModel,
    PaiementModel,
)
from contexts.service_ventes.tests.conftest import (
    inscrire_produit_via_api,
    ouvrir_addition_via_api,
    ouvrir_service_via_api,
)
from shared.infrastructure.journal.models import MouvementModel


def _vendre(client: APIClient, service_id: str, addition_id: str, *, montant: int) -> None:
    produit_id = inscrire_produit_via_api(client, prix=montant)
    reponse = client.post(
        f"/api/services/{service_id}/ventes/",
        {
            "produit_id": produit_id,
            "quantite": 1,
            "forme_paiement": "especes",
            "addition_id": addition_id,
        },
        format="json",
    )
    assert reponse.status_code == 201


def _payer(client: APIClient, service_id: str, addition_id: str, montant: int) -> Any:
    return client.post(
        f"/api/services/{service_id}/additions/{addition_id}/paiements/",
        {"montant": montant, "forme_paiement": "especes"},
        format="json",
    )


def _addition(client: APIClient, service_id: str, addition_id: str) -> Any:
    reponse = client.get(f"/api/services/{service_id}/additions/{addition_id}/")
    assert reponse.status_code == 200
    return reponse.json()


@pytest.mark.django_db
def test_un_paiement_partiel_laisse_l_addition_ouverte(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=2_000)

    reponse = _payer(client_api, service_id, addition_id, 500)

    assert reponse.status_code == 201
    assert reponse.json()["reste_a_payer"] == 1_500
    corps = _addition(client_api, service_id, addition_id)
    assert corps["paye"] == 500
    assert corps["reste_a_payer"] == 1_500
    assert corps["statut"] == "ouverte"


@pytest.mark.django_db
def test_payer_le_solde_regle_l_addition(client_api: APIClient) -> None:
    """Le règlement est une conséquence du paiement, pas une déclaration."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=2_000)
    _payer(client_api, service_id, addition_id, 500)

    reponse = _payer(client_api, service_id, addition_id, 1_500)

    assert reponse.status_code == 201
    assert reponse.json()["reste_a_payer"] == 0
    assert AdditionModel.objects.get(pk=addition_id).statut == "reglee"
    corps = _addition(client_api, service_id, addition_id)
    assert corps["statut"] == "reglee"
    assert corps["paye"] == 2_000
    assert len(corps["paiements"]) == 2


@pytest.mark.django_db
def test_le_reglement_et_le_paiement_sont_journalises(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=1_000)

    _payer(client_api, service_id, addition_id, 1_000)

    assert MouvementModel.objects.filter(type="PaiementRecu").count() == 1
    assert MouvementModel.objects.filter(type="AdditionReglee").count() == 1


@pytest.mark.django_db
def test_payer_plus_que_le_reste_du_est_refuse(client_api: APIClient) -> None:
    """Rendre la monnaie est un autre Fait, pas un paiement gonflé."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=1_000)

    reponse = _payer(client_api, service_id, addition_id, 1_500)

    assert reponse.status_code == 409
    assert "1000" in reponse.json()["detail"].replace(" ", "")
    assert PaiementModel.objects.count() == 0


@pytest.mark.django_db
def test_payer_une_addition_deja_reglee_est_refuse(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=1_000)
    _payer(client_api, service_id, addition_id, 1_000)

    reponse = _payer(client_api, service_id, addition_id, 100)

    assert reponse.status_code == 409
    assert PaiementModel.objects.count() == 1


@pytest.mark.django_db
def test_un_montant_nul_est_refuse(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=1_000)

    reponse = _payer(client_api, service_id, addition_id, 0)

    assert reponse.status_code == 400


@pytest.mark.django_db
def test_payer_sur_une_addition_d_un_autre_service_retourne_404(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    autre_service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = _payer(client_api, autre_service_id, addition_id, 100)

    assert reponse.status_code == 404
    assert PaiementModel.objects.count() == 0


@pytest.mark.django_db
def test_clore_une_addition_non_soldee_est_refuse(client_api: APIClient) -> None:
    """Le trou que cette tranche ferme : clore sans avoir encaissé."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=2_000)
    _payer(client_api, service_id, addition_id, 500)

    reponse = client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    assert reponse.status_code == 409
    assert "1500" in reponse.json()["detail"].replace(" ", "")
    assert AdditionModel.objects.get(pk=addition_id).statut == "ouverte"


@pytest.mark.django_db
def test_une_addition_sans_consommation_peut_etre_close(client_api: APIClient) -> None:
    """Une table qui n'a rien consommé ne doit rien : on peut clore."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "reglee"


@pytest.mark.django_db
def test_une_addition_soldee_n_empeche_plus_la_cloture_du_service(client_api: APIClient) -> None:
    """Bout en bout : servir, encaisser, clôturer la journée."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _vendre(client_api, service_id, addition_id, montant=1_300)
    _payer(client_api, service_id, addition_id, 1_300)

    reponse = client_api.post(f"/api/services/{service_id}/cloture/", format="json")

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "cloture"
