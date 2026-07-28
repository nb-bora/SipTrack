"""Test d'intégration : « Rattacher les ventes à une addition » de bout en bout."""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.infrastructure.django_app.models import AdditionModel, VenteModel


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
    result = reponse.json()
    assert isinstance(result, dict)
    service_id = result["id"]
    assert isinstance(service_id, str)
    return service_id


def _ouvrir_addition(client: APIClient, service_id: str, table_numero: int = 5) -> str:
    reponse = client.post(
        f"/api/services/{service_id}/additions/",
        {"auteur_id": "u1", "table_numero": table_numero},
        format="json",
    )
    assert reponse.status_code == 201
    result = reponse.json()
    assert isinstance(result, dict)
    addition_id = result["id"]
    assert isinstance(addition_id, str)
    return addition_id


def _vendre(
    client: APIClient,
    service_id: str,
    *,
    addition_id: str | None = None,
    quantite: int = 2,
    prix_unitaire: int = 650,
) -> Any:
    corps: dict[str, Any] = {
        "auteur_id": "u1",
        "produit_id": "33export",
        "quantite": quantite,
        "prix_unitaire": prix_unitaire,
        "forme_paiement": "especes",
    }
    if addition_id is not None:
        corps["addition_id"] = addition_id
    return client.post(f"/api/services/{service_id}/ventes/", corps, format="json")


@pytest.mark.django_db
def test_une_vente_rattachee_a_une_addition_est_persistee_avec_son_addition() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    reponse = _vendre(client, service_id, addition_id=addition_id)

    assert reponse.status_code == 201
    assert reponse.json()["addition_id"] == addition_id
    vente_en_db = VenteModel.objects.get(pk=reponse.json()["id"])
    assert vente_en_db.addition_id == addition_id


@pytest.mark.django_db
def test_le_total_d_une_addition_est_la_somme_de_ses_lignes() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    assert _vendre(client, service_id, addition_id=addition_id, quantite=2).status_code == 201
    assert (
        _vendre(
            client,
            service_id,
            addition_id=addition_id,
            quantite=1,
            prix_unitaire=1_000,
        ).status_code
        == 201
    )
    # Une vente au comptoir ne doit pas peser sur l'addition de la table.
    assert _vendre(client, service_id, quantite=4).status_code == 201

    reponse = client.get(f"/api/services/{service_id}/additions/{addition_id}/")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["table_numero"] == 5
    assert corps["statut"] == "ouverte"
    assert len(corps["lignes"]) == 2
    assert corps["total"] == 2 * 650 + 1_000


@pytest.mark.django_db
def test_une_addition_sans_consommation_a_un_total_nul() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    reponse = client.get(f"/api/services/{service_id}/additions/{addition_id}/")

    assert reponse.status_code == 200
    assert reponse.json()["lignes"] == []
    assert reponse.json()["total"] == 0


@pytest.mark.django_db
def test_lire_une_addition_introuvable_retourne_404() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    reponse = client.get(f"/api/services/{service_id}/additions/add-inexistante/")

    assert reponse.status_code == 404
    assert "introuvable" in reponse.json()["detail"].lower()


@pytest.mark.django_db
def test_lire_une_addition_depuis_un_autre_service_retourne_404() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    autre_service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    reponse = client.get(f"/api/services/{autre_service_id}/additions/{addition_id}/")

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_vendre_sur_une_addition_introuvable_retourne_404() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)

    reponse = _vendre(client, service_id, addition_id="add-inexistante")

    assert reponse.status_code == 404
    assert "addition" in reponse.json()["detail"].lower()
    assert VenteModel.objects.count() == 0


@pytest.mark.django_db
def test_vendre_sur_une_addition_d_un_autre_service_retourne_404() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    autre_service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    reponse = _vendre(client, autre_service_id, addition_id=addition_id)

    assert reponse.status_code == 404
    assert VenteModel.objects.count() == 0


@pytest.mark.django_db
def test_vendre_sur_une_addition_deja_reglee_retourne_409() -> None:
    client = APIClient()
    service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)

    reponse_reglement = client.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        {"auteur_id": "u1"},
        format="json",
    )
    assert reponse_reglement.status_code == 200

    reponse = _vendre(client, service_id, addition_id=addition_id)

    assert reponse.status_code == 409
    assert "clôturée" in reponse.json()["detail"].lower()
    assert VenteModel.objects.count() == 0


@pytest.mark.django_db
def test_le_total_reste_calcule_apres_reglement() -> None:
    """Une addition réglée reste lisible : le total se recalcule depuis ses lignes."""
    client = APIClient()
    service_id = _ouvrir_service(client)
    addition_id = _ouvrir_addition(client, service_id)
    assert _vendre(client, service_id, addition_id=addition_id, quantite=3).status_code == 201

    client.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        {"auteur_id": "u1"},
        format="json",
    )

    reponse = client.get(f"/api/services/{service_id}/additions/{addition_id}/")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["statut"] == "reglee"
    assert corps["total"] == 3 * 650
    assert AdditionModel.objects.get(pk=addition_id).statut == "reglee"
