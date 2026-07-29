"""Test d'intégration : « Le prix vient du catalogue » de bout en bout.

Le trou que cette tranche ferme : `prix_unitaire` était lu dans le corps de la
requête. La personne qui saisit décidait de ce que la consommation avait valu —
et la réconciliation de fin de service tombait juste, puisqu'elle comparait deux
chiffres qu'elle avait elle-même choisis.
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


def _vendre(
    client: APIClient,
    service_id: str,
    produit_id: str,
    *,
    quantite: int = 1,
    extra: dict[str, Any] | None = None,
) -> Any:
    corps: dict[str, Any] = {
        "produit_id": produit_id,
        "quantite": quantite,
        "forme_paiement": "especes",
    }
    corps.update(extra or {})
    return client.post(f"/api/services/{service_id}/ventes/", corps, format="json")


@pytest.mark.django_db
def test_le_prix_vient_du_catalogue(client_api: APIClient) -> None:
    """Le cœur de la tranche."""
    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    reponse = _vendre(client_api, service_id, produit_id, quantite=3)

    assert reponse.status_code == 201
    assert reponse.json()["prix_unitaire"] == 1_000
    assert reponse.json()["montant_total"] == 3_000


@pytest.mark.django_db
def test_un_prix_envoye_avec_la_vente_est_ignore(client_api: APIClient) -> None:
    """Le garde-fou : même en le glissant dans le corps, on ne fixe pas son prix."""
    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    reponse = _vendre(client_api, service_id, produit_id, extra={"prix_unitaire": 600})

    assert reponse.status_code == 201
    assert reponse.json()["prix_unitaire"] == 1_000
    assert reponse.json()["montant_total"] == 1_000


@pytest.mark.django_db
def test_la_sous_caisse_attend_le_vrai_prix(client_api: APIClient) -> None:
    """Le scénario complet du vol que cette tranche rend impossible.

    Avant : la serveuse saisissait 600, encaissait 1 000, versait 600, écart nul.
    Maintenant : la vente vaut 1 000 quoi qu'elle envoie, donc l'attendu aussi.
    """
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)
    _vendre(
        client_api, service_id, produit_id, extra={"prix_unitaire": 600, "addition_id": addition_id}
    )
    client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/paiements/",
        {"montant": 1_000, "forme_paiement": "especes"},
        format="json",
    )

    # Elle ne verse que ce qu'elle aurait gardé si le prix minoré avait pris.
    reponse = client_api.post(
        f"/api/services/{service_id}/versement/", {"montant": 600}, format="json"
    )

    assert reponse.json()["attendu"] == 1_000
    assert reponse.json()["ecart"] == -400  # le manquant apparaît
    assert MouvementModel.objects.filter(type="EcartConstate").count() == 1


@pytest.mark.django_db
def test_vendre_un_produit_inconnu_est_refuse(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)

    reponse = _vendre(client_api, service_id, "inexistant")

    assert reponse.status_code == 409
    assert MouvementModel.objects.filter(type="VenteEnregistree").count() == 0


@pytest.mark.django_db
def test_vendre_un_produit_d_un_autre_bar_est_refuse(
    client_api: APIClient, autre_bar_de_test: str
) -> None:
    """Le catalogue de l'un ne fixe pas les prix de l'autre.

    Les deux bars appartiennent ici à la même personne : la frontière éprouvée
    est celle du catalogue, pas celle des droits.
    """
    service_id = ouvrir_service_via_api(client_api)  # bar1
    produit_id = inscrire_produit_via_api(client_api, prix=1_000, bar_id=autre_bar_de_test)

    reponse = _vendre(client_api, service_id, produit_id)

    assert reponse.status_code == 409


@pytest.mark.django_db
def test_vendre_un_produit_retire_est_refuse(client_api: APIClient) -> None:
    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)
    assert client_api.post(f"/api/produits/{produit_id}/retrait/").status_code == 200

    reponse = _vendre(client_api, service_id, produit_id)

    assert reponse.status_code == 409


@pytest.mark.django_db
def test_changer_le_tarif_ne_touche_pas_les_ventes_passees(client_api: APIClient) -> None:
    """Une vente d'hier garde le prix d'hier."""
    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)
    vente = _vendre(client_api, service_id, produit_id).json()

    client_api.post(f"/api/produits/{produit_id}/tarif/", {"prix": 1_500}, format="json")

    apres = _vendre(client_api, service_id, produit_id).json()
    assert vente["prix_unitaire"] == 1_000  # inchangée
    assert apres["prix_unitaire"] == 1_500  # la suivante suit le nouveau tarif


@pytest.mark.django_db
def test_le_changement_de_tarif_est_un_fait_attribue(client_api: APIClient, auteur: Any) -> None:
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    reponse = client_api.post(f"/api/produits/{produit_id}/tarif/", {"prix": 1_500}, format="json")

    assert reponse.status_code == 200
    mouvement = MouvementModel.objects.get(type="TarifModifie")
    assert mouvement.auteur_id == str(auteur.pk)
    assert mouvement.donnees["ancien_prix"] == 1_000
    assert mouvement.donnees["nouveau_prix"] == 1_500


@pytest.mark.django_db
def test_inscrire_deux_fois_le_meme_nom_est_refuse(client_api: APIClient) -> None:
    """Deux lignes pour la même bière rendraient tout comptage ambigu."""
    inscrire_produit_via_api(client_api, prix=1_000, nom="33 Export")

    reponse = client_api.post(
        "/api/produits/", {"bar_id": "bar1", "nom": "33 Export", "prix": 600}, format="json"
    )

    assert reponse.status_code == 409


@pytest.mark.django_db
def test_le_catalogue_montre_les_produits_retires(client_api: APIClient) -> None:
    """Ils restent visibles, marqués : les ventes passées les référencent."""
    produit_id = inscrire_produit_via_api(client_api, prix=1_000, nom="Castel")
    client_api.post(f"/api/produits/{produit_id}/retrait/")

    catalogue = client_api.get("/api/bars/bar1/produits/").json()

    assert len(catalogue) == 1
    assert catalogue[0]["nom"] == "Castel"
    assert catalogue[0]["en_vente"] is False


@pytest.mark.django_db
def test_reappliquer_le_meme_tarif_est_refuse(client_api: APIClient) -> None:
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    reponse = client_api.post(f"/api/produits/{produit_id}/tarif/", {"prix": 1_000}, format="json")

    assert reponse.status_code == 409
    assert MouvementModel.objects.filter(type="TarifModifie").count() == 0


@pytest.mark.django_db
def test_tarifer_un_produit_inexistant_retourne_404(client_api: APIClient) -> None:
    reponse = client_api.post("/api/produits/inexistant/tarif/", {"prix": 1_000}, format="json")

    assert reponse.status_code == 404
