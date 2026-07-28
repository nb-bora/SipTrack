"""Test d'intégration : « Rattacher les ventes à une addition » de bout en bout."""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import AdditionModel, VenteModel
from contexts.service_ventes.tests.conftest import (
    ouvrir_addition_via_api,
    ouvrir_service_via_api,
)


def _vendre(
    client: APIClient,
    service_id: str,
    *,
    addition_id: str | None = None,
    quantite: int = 2,
    prix_unitaire: int = 650,
) -> Any:
    corps: dict[str, Any] = {
        "produit_id": "33export",
        "quantite": quantite,
        "prix_unitaire": prix_unitaire,
        "forme_paiement": "especes",
    }
    if addition_id is not None:
        corps["addition_id"] = addition_id
    return client.post(f"/api/services/{service_id}/ventes/", corps, format="json")


@pytest.mark.django_db
def test_une_vente_rattachee_a_une_addition_est_persistee_avec_son_addition(
    client_api: APIClient,
) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = _vendre(client_api, service_id, addition_id=addition_id)

    assert reponse.status_code == 201
    assert reponse.json()["addition_id"] == addition_id
    vente_en_db = VenteModel.objects.get(pk=reponse.json()["id"])
    assert vente_en_db.addition_id == addition_id


@pytest.mark.django_db
def test_le_total_d_une_addition_est_la_somme_de_ses_lignes(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    assert _vendre(client_api, service_id, addition_id=addition_id, quantite=2).status_code == 201
    assert (
        _vendre(
            client_api,
            service_id,
            addition_id=addition_id,
            quantite=1,
            prix_unitaire=1_000,
        ).status_code
        == 201
    )
    # Une vente au comptoir ne doit pas peser sur l'addition de la table.
    assert _vendre(client_api, service_id, quantite=4).status_code == 201

    reponse = client_api.get(f"/api/services/{service_id}/additions/{addition_id}/")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["table_numero"] == 5
    assert corps["statut"] == "ouverte"
    assert len(corps["lignes"]) == 2
    assert corps["total"] == 2 * 650 + 1_000


@pytest.mark.django_db
def test_une_addition_sans_consommation_a_un_total_nul(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = client_api.get(f"/api/services/{service_id}/additions/{addition_id}/")

    assert reponse.status_code == 200
    assert reponse.json()["lignes"] == []
    assert reponse.json()["total"] == 0


@pytest.mark.django_db
def test_lire_une_addition_introuvable_retourne_404(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    reponse = client_api.get(f"/api/services/{service_id}/additions/add-inexistante/")

    assert reponse.status_code == 404
    assert "introuvable" in reponse.json()["detail"].lower()


@pytest.mark.django_db
def test_lire_une_addition_depuis_un_autre_service_retourne_404(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    autre_service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = client_api.get(f"/api/services/{autre_service_id}/additions/{addition_id}/")

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_vendre_sur_une_addition_introuvable_retourne_404(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    reponse = _vendre(client_api, service_id, addition_id="add-inexistante")

    assert reponse.status_code == 404
    assert "addition" in reponse.json()["detail"].lower()
    assert VenteModel.objects.count() == 0


@pytest.mark.django_db
def test_vendre_sur_une_addition_d_un_autre_service_retourne_404(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    autre_service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse = _vendre(client_api, autre_service_id, addition_id=addition_id)

    assert reponse.status_code == 404
    assert VenteModel.objects.count() == 0


@pytest.mark.django_db
def test_vendre_sur_une_addition_deja_reglee_retourne_409(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)

    reponse_reglement = client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )
    assert reponse_reglement.status_code == 200

    reponse = _vendre(client_api, service_id, addition_id=addition_id)

    assert reponse.status_code == 409
    assert "clôturée" in reponse.json()["detail"].lower()
    assert VenteModel.objects.count() == 0


@pytest.mark.django_db
def test_le_total_reste_calcule_apres_reglement(client_api: APIClient) -> None:
    """Une addition réglée reste lisible : le total se recalcule depuis ses lignes."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    assert _vendre(client_api, service_id, addition_id=addition_id, quantite=3).status_code == 201

    client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    reponse = client_api.get(f"/api/services/{service_id}/additions/{addition_id}/")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["statut"] == "reglee"
    assert corps["total"] == 3 * 650
    assert AdditionModel.objects.get(pk=addition_id).statut == "reglee"
