"""Test d'intégration : « Sous-caisse serveuse » de bout en bout.

La réconciliation quotidienne du modèle métier (§9) : ce qu'une serveuse a
encaissé face à ce qu'elle remet.
"""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.tests.conftest import (
    inscrire_produit_via_api,
    ouvrir_addition_via_api,
    ouvrir_service_via_api,
)
from shared.infrastructure.journal.models import MouvementModel


def _servir_et_encaisser(
    client: APIClient,
    service_id: str,
    *,
    montant: int,
    forme: str = "especes",
    table: int = 5,
) -> None:
    addition_id = ouvrir_addition_via_api(client, service_id, table_numero=table)
    produit_id = inscrire_produit_via_api(client, prix=montant)
    reponse = client.post(
        f"/api/services/{service_id}/ventes/",
        {
            "produit_id": produit_id,
            "quantite": 1,
            "forme_paiement": forme,
            "addition_id": addition_id,
        },
        format="json",
    )
    assert reponse.status_code == 201
    reponse = client.post(
        f"/api/services/{service_id}/additions/{addition_id}/paiements/",
        {"montant": montant, "forme_paiement": forme},
        format="json",
    )
    assert reponse.status_code == 201


def _verser(client: APIClient, service_id: str, montant: int) -> Any:
    return client.post(
        f"/api/services/{service_id}/versement/",
        {"montant": montant},
        format="json",
    )


def _sous_caisses(client: APIClient, service_id: str) -> Any:
    reponse = client.get(f"/api/services/{service_id}/sous-caisses/")
    assert reponse.status_code == 200
    return reponse.json()


@pytest.mark.django_db
def test_une_recette_juste_ne_produit_aucun_ecart(client_api: APIClient, auteur: Any) -> None:
    service_id = ouvrir_service_via_api(client_api)
    _servir_et_encaisser(client_api, service_id, montant=1_300, table=1)
    _servir_et_encaisser(client_api, service_id, montant=700, table=2)

    reponse = _verser(client_api, service_id, 2_000)

    assert reponse.status_code == 201
    corps = reponse.json()
    assert corps["attendu"] == 2_000
    assert corps["verse"] == 2_000
    assert corps["ecart"] == 0
    assert corps["serveuse_id"] == str(auteur.pk)
    # Pas d'écart : pas de Fait d'écart.
    assert MouvementModel.objects.filter(type="RecetteVersee").count() == 1
    assert MouvementModel.objects.filter(type="EcartConstate").count() == 0


@pytest.mark.django_db
def test_un_manquant_est_constate_comme_fait(client_api: APIClient) -> None:
    """Le cœur du contrôle : l'écart ne se perd pas, il s'écrit."""
    service_id = ouvrir_service_via_api(client_api)
    _servir_et_encaisser(client_api, service_id, montant=2_000)

    reponse = _verser(client_api, service_id, 1_500)

    assert reponse.status_code == 201
    assert reponse.json()["ecart"] == -500
    assert MouvementModel.objects.filter(type="EcartConstate").count() == 1


@pytest.mark.django_db
def test_un_excedent_est_constate_aussi(client_api: APIClient) -> None:
    """Un excédent est tout aussi inexpliqué qu'un manquant."""
    service_id = ouvrir_service_via_api(client_api)
    _servir_et_encaisser(client_api, service_id, montant=1_000)

    reponse = _verser(client_api, service_id, 1_200)

    assert reponse.json()["ecart"] == 200
    assert MouvementModel.objects.filter(type="EcartConstate").count() == 1


@pytest.mark.django_db
def test_un_ecart_d_un_franc_est_constate(client_api: APIClient) -> None:
    """« Zéro inexpliqué » : aucun seuil de tolérance (invariant 4)."""
    service_id = ouvrir_service_via_api(client_api)
    _servir_et_encaisser(client_api, service_id, montant=1_000)

    reponse = _verser(client_api, service_id, 999)

    assert reponse.json()["ecart"] == -1
    assert MouvementModel.objects.filter(type="EcartConstate").count() == 1


@pytest.mark.django_db
def test_le_mobile_money_n_entre_pas_dans_l_attendu(client_api: APIClient) -> None:
    """Il n'est pas remis de la main à la main : l'exiger créerait un faux manquant."""
    service_id = ouvrir_service_via_api(client_api)
    _servir_et_encaisser(client_api, service_id, montant=1_000, table=1)
    _servir_et_encaisser(client_api, service_id, montant=5_000, forme="mobile_money", table=2)

    reponse = _verser(client_api, service_id, 1_000)

    assert reponse.json()["attendu"] == 1_000
    assert reponse.json()["ecart"] == 0
    caisses = _sous_caisses(client_api, service_id)
    assert caisses[0]["encaisse_especes"] == 1_000
    assert caisses[0]["encaisse_mobile_money"] == 5_000


@pytest.mark.django_db
def test_verser_deux_fois_est_refuse(client_api: APIClient) -> None:
    """Un second versement masquerait le premier : la correction se contre-passe."""
    service_id = ouvrir_service_via_api(client_api)
    _servir_et_encaisser(client_api, service_id, montant=1_000)
    assert _verser(client_api, service_id, 1_000).status_code == 201

    reponse = _verser(client_api, service_id, 500)

    assert reponse.status_code == 409
    assert MouvementModel.objects.filter(type="RecetteVersee").count() == 1


@pytest.mark.django_db
def test_verser_sur_un_service_cloture_est_refuse(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    assert client_api.post(f"/api/services/{service_id}/cloture/", format="json").status_code == 200

    reponse = _verser(client_api, service_id, 1_000)

    assert reponse.status_code == 409


@pytest.mark.django_db
def test_verser_sur_un_service_inexistant_retourne_404(client_api: APIClient) -> None:
    reponse = _verser(client_api, "inexistant", 1_000)

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_la_vue_gerante_montre_le_du_avant_versement(client_api: APIClient, auteur: Any) -> None:
    service_id = ouvrir_service_via_api(client_api)
    _servir_et_encaisser(client_api, service_id, montant=1_300)

    caisses = _sous_caisses(client_api, service_id)

    assert len(caisses) == 1
    assert caisses[0]["serveuse_id"] == str(auteur.pk)
    assert caisses[0]["encaisse_especes"] == 1_300
    # Tant qu'elle n'a pas versé, il n'y a ni versement ni écart — pas un zéro.
    assert caisses[0]["verse"] is None
    assert caisses[0]["ecart"] is None


@pytest.mark.django_db
def test_la_vue_gerante_est_vide_sans_encaissement(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    assert _sous_caisses(client_api, service_id) == []
