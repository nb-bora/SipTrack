"""Test d'intégration : « Crédit client » de bout en bout.

Le trou que cette tranche ferme : jusqu'ici, `forme_paiement = "credit"` réglait
l'addition sans qu'aucun argent n'entre **et sans que personne ne doive rien**.
La consommation s'évaporait du décompte.
"""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from contexts.credit_creances.tests.conftest import creer_client_via_api
from contexts.service_ventes.tests.conftest import (
    inscrire_produit_via_api,
    ouvrir_addition_via_api,
    ouvrir_service_via_api,
)
from shared.infrastructure.journal.models import MouvementModel


def _servir(client: APIClient, service_id: str, addition_id: str, montant: int) -> None:
    produit_id = inscrire_produit_via_api(client, prix=montant)
    reponse = client.post(
        f"/api/services/{service_id}/ventes/",
        {
            "produit_id": produit_id,
            "quantite": 1,
            "forme_paiement": "credit",
            "addition_id": addition_id,
        },
        format="json",
    )
    assert reponse.status_code == 201


def _payer(
    client: APIClient,
    service_id: str,
    addition_id: str,
    montant: int,
    *,
    forme: str = "credit",
    client_id: str | None = None,
) -> Any:
    corps: dict[str, Any] = {"montant": montant, "forme_paiement": forme}
    if client_id is not None:
        corps["client_id"] = client_id
    return client.post(
        f"/api/services/{service_id}/additions/{addition_id}/paiements/",
        corps,
        format="json",
    )


def _addition_a_credit(client: APIClient, montant: int = 5_000) -> tuple[str, str, str]:
    """Sert une table, la fait partir en crédit, et renvoie (service, addition, client)."""
    service_id = ouvrir_service_via_api(client)
    addition_id = ouvrir_addition_via_api(client, service_id)
    _servir(client, service_id, addition_id, montant)
    client_id = creer_client_via_api(client)
    reponse = _payer(client, service_id, addition_id, montant, client_id=client_id)
    assert reponse.status_code == 201
    return service_id, addition_id, client_id


def _encours(client: APIClient, client_id: str) -> Any:
    reponse = client.get(f"/api/clients/{client_id}/encours/")
    assert reponse.status_code == 200
    return reponse.json()


@pytest.mark.django_db
def test_un_credit_laisse_une_dette_derriere_lui(client_api: APIClient) -> None:
    """Le cœur de la tranche : l'argent ne disparaît plus sans débiteur."""
    _service_id, addition_id, client_id = _addition_a_credit(client_api, 5_000)

    encours = _encours(client_api, client_id)

    assert encours["reste"] == 5_000
    assert len(encours["creances"]) == 1
    assert encours["creances"][0]["addition_id"] == addition_id
    assert encours["creances"][0]["statut"] == "ne"
    assert MouvementModel.objects.filter(type="CreditAccorde").count() == 1


@pytest.mark.django_db
def test_un_credit_libere_la_table_malgre_la_dette(client_api: APIClient) -> None:
    """La table est rendue, la consommation est comptée : c'est la créance —
    pas l'addition — qui reste ouverte."""
    service_id, addition_id, _client_id = _addition_a_credit(client_api)

    reponse = client_api.get(f"/api/services/{service_id}/additions/{addition_id}/")

    assert reponse.json()["statut"] == "reglee"
    # Et le service peut donc se clôturer : un client à crédit ne bloque pas la nuit.
    assert client_api.post(f"/api/services/{service_id}/cloture/").status_code == 200


@pytest.mark.django_db
def test_un_credit_sans_client_est_refuse(client_api: APIClient) -> None:
    """Un crédit sans débiteur, c'est exactement le trou qu'on ferme."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _servir(client_api, service_id, addition_id, 5_000)

    reponse = _payer(client_api, service_id, addition_id, 5_000)

    assert reponse.status_code == 409
    assert MouvementModel.objects.filter(type="PaiementRecu").count() == 0


@pytest.mark.django_db
def test_un_credit_au_nom_d_un_client_inconnu_est_refuse(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _servir(client_api, service_id, addition_id, 5_000)

    reponse = _payer(client_api, service_id, addition_id, 5_000, client_id="inexistant")

    assert reponse.status_code == 409
    assert MouvementModel.objects.filter(type="CreditAccorde").count() == 0
    # Rien n'a été encaissé non plus : la transaction est annulée en entier.
    assert MouvementModel.objects.filter(type="PaiementRecu").count() == 0


@pytest.mark.django_db
def test_un_remboursement_partiel_reduit_l_encours(client_api: APIClient) -> None:
    _service_id, _addition_id, client_id = _addition_a_credit(client_api, 5_000)
    credit_id = _encours(client_api, client_id)["creances"][0]["credit_id"]

    reponse = client_api.post(
        f"/api/credits/{credit_id}/remboursements/", {"montant": 2_000}, format="json"
    )

    assert reponse.status_code == 201
    assert reponse.json()["reste"] == 3_000
    assert reponse.json()["statut"] == "ne"
    assert _encours(client_api, client_id)["reste"] == 3_000


@pytest.mark.django_db
def test_le_dernier_remboursement_eteint_la_dette(client_api: APIClient) -> None:
    _service_id, _addition_id, client_id = _addition_a_credit(client_api, 5_000)
    credit_id = _encours(client_api, client_id)["creances"][0]["credit_id"]
    client_api.post(f"/api/credits/{credit_id}/remboursements/", {"montant": 3_000}, format="json")

    reponse = client_api.post(
        f"/api/credits/{credit_id}/remboursements/", {"montant": 2_000}, format="json"
    )

    assert reponse.json()["statut"] == "solde"
    assert reponse.json()["reste"] == 0
    assert MouvementModel.objects.filter(type="CreditSolde").count() == 1
    assert MouvementModel.objects.filter(type="RemboursementRecu").count() == 2


@pytest.mark.django_db
def test_rembourser_plus_que_le_du_est_refuse(client_api: APIClient) -> None:
    _service_id, _addition_id, client_id = _addition_a_credit(client_api, 5_000)
    credit_id = _encours(client_api, client_id)["creances"][0]["credit_id"]

    reponse = client_api.post(
        f"/api/credits/{credit_id}/remboursements/", {"montant": 6_000}, format="json"
    )

    assert reponse.status_code == 409
    assert reponse.json()["reste"] == 5_000


@pytest.mark.django_db
def test_rembourser_un_credit_inexistant_retourne_404(client_api: APIClient) -> None:
    reponse = client_api.post(
        "/api/credits/inexistant/remboursements/", {"montant": 500}, format="json"
    )

    assert reponse.status_code == 404


@pytest.mark.django_db
def test_chaque_remboursement_dit_qui_l_a_encaisse(client_api: APIClient, auteur: Any) -> None:
    _service_id, _addition_id, client_id = _addition_a_credit(client_api, 5_000)
    credit_id = _encours(client_api, client_id)["creances"][0]["credit_id"]

    client_api.post(f"/api/credits/{credit_id}/remboursements/", {"montant": 1_000}, format="json")

    mouvement = MouvementModel.objects.get(type="RemboursementRecu")
    assert mouvement.auteur_id == str(auteur.pk)


@pytest.mark.django_db
def test_un_meme_nom_ne_cree_pas_deux_clients(client_api: APIClient) -> None:
    """Sinon une même personne porterait deux dettes séparées."""
    premier = creer_client_via_api(client_api, nom="Jean")
    second = creer_client_via_api(client_api, nom="Jean")

    assert premier == second


@pytest.mark.django_db
def test_la_vue_gerante_ne_montre_que_les_dettes_vivantes(client_api: APIClient) -> None:
    _service_id, _addition_id, client_id = _addition_a_credit(client_api, 5_000)
    credit_id = _encours(client_api, client_id)["creances"][0]["credit_id"]

    avant = client_api.get("/api/bars/bar1/encours/").json()
    assert len(avant) == 1
    assert avant[0]["reste"] == 5_000

    client_api.post(f"/api/credits/{credit_id}/remboursements/", {"montant": 5_000}, format="json")

    assert client_api.get("/api/bars/bar1/encours/").json() == []


@pytest.mark.django_db
def test_les_especes_restent_du_ressort_de_la_sous_caisse(client_api: APIClient) -> None:
    """Un crédit n'est pas de l'argent remis : il ne doit rien attendre de la serveuse."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    _servir(client_api, service_id, addition_id, 5_000)
    client_id = creer_client_via_api(client_api)
    _payer(client_api, service_id, addition_id, 5_000, client_id=client_id)

    reponse = client_api.post(
        f"/api/services/{service_id}/versement/", {"montant": 0}, format="json"
    )

    assert reponse.json()["attendu"] == 0
    assert reponse.json()["ecart"] == 0
