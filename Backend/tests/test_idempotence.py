"""Un rejeu ne doit jamais créer un second fait.

L'app mobile est offline-first. À la reconnexion, une requête partie en timeout
est rejouée — c'est le comportement correct d'un client hors ligne, pas un
défaut. Sans protection, deux ventes naissent d'une seule consommation, et le
journal étant immuable, ce doublon ne se défait pas : il gonfle la recette
attendue et la réconciliation accusera une serveuse qui n'a rien fait.

Distinct de la concurrence sur contrainte unique, déjà traitée : une serveuse
peut légitimement saisir deux fois la même bière au même prix. Seule une clé
fournie par le client distingue « deux consommations » de « deux fois la même
requête ».
"""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from contexts.service_ventes.tests.conftest import (
    inscrire_produit_via_api,
    ouvrir_service_via_api,
)


def _vendre(client: APIClient, service_id: str, produit_id: str, *, cle: str) -> Any:
    return client.post(
        f"/api/services/{service_id}/ventes/",
        {"produit_id": produit_id, "quantite": 1, "forme_paiement": "especes"},
        format="json",
        headers={"Idempotency-Key": cle},
    )


@pytest.mark.django_db
def test_rejouer_une_vente_ne_cree_pas_un_second_fait(client_api: APIClient) -> None:
    """Le cas qui corrompt les données sans que personne ne fasse rien de mal."""
    from contexts.service_ventes.infrastructure.django_app.models import VenteModel

    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    premiere = _vendre(client_api, service_id, produit_id, cle="cle-reseau-instable")
    seconde = _vendre(client_api, service_id, produit_id, cle="cle-reseau-instable")

    assert premiere.status_code == 201
    assert seconde.status_code == 201
    assert VenteModel.objects.count() == 1


@pytest.mark.django_db
def test_le_rejeu_rend_exactement_la_meme_reponse(client_api: APIClient) -> None:
    """Le client doit pouvoir traiter la réponse rejouée comme la première.

    Sans cela, l'app mobile croirait la vente perdue et la ferait ressaisir à la
    main — le doublon reviendrait par la porte de l'utilisateur.
    """
    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    premiere = _vendre(client_api, service_id, produit_id, cle="meme-cle")
    seconde = _vendre(client_api, service_id, produit_id, cle="meme-cle")

    assert seconde.json() == premiere.json()


@pytest.mark.django_db
def test_deux_ventes_distinctes_passent_toutes_les_deux(client_api: APIClient) -> None:
    """La contrepartie : deux clés différentes sont deux faits différents.

    Une serveuse sert légitimement deux fois la même bière. Sans ce test, une
    protection trop large ferait disparaître des ventes réelles — bien pire que
    le problème qu'elle résout.
    """
    from contexts.service_ventes.infrastructure.django_app.models import VenteModel

    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    _vendre(client_api, service_id, produit_id, cle="premiere-tournee")
    _vendre(client_api, service_id, produit_id, cle="seconde-tournee")

    assert VenteModel.objects.count() == 2


@pytest.mark.django_db
def test_reutiliser_une_cle_pour_une_autre_requete_est_refuse(client_api: APIClient) -> None:
    """Une clé désigne une écriture précise, pas un appelant.

    Rendre la réponse mémorisée à une requête différente serait un mensonge : le
    client croirait avoir enregistré une vente qui n'a jamais eu lieu.
    """
    service_id = ouvrir_service_via_api(client_api)
    premier = inscrire_produit_via_api(client_api, prix=1_000)
    second = inscrire_produit_via_api(client_api, prix=5_000)

    _vendre(client_api, service_id, premier, cle="cle-recyclee")
    reponse = _vendre(client_api, service_id, second, cle="cle-recyclee")

    assert reponse.status_code == 422


@pytest.mark.django_db
def test_le_rejeu_s_annonce_dans_la_reponse(client_api: APIClient) -> None:
    """Le client doit pouvoir distinguer « enregistré » de « déjà enregistré ».

    Les deux réponses sont identiques par construction ; sans cet en-tête, une
    app qui compte ses envois ne saurait jamais lesquels ont abouti du premier
    coup.
    """
    from shared.infrastructure.idempotence.middleware import EN_TETE_REJEU

    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    premiere = _vendre(client_api, service_id, produit_id, cle="cle-annoncee")
    seconde = _vendre(client_api, service_id, produit_id, cle="cle-annoncee")

    assert EN_TETE_REJEU not in premiere.headers
    assert seconde.headers[EN_TETE_REJEU] == "true"


@pytest.mark.django_db
def test_une_requete_concurrente_est_invitee_a_reessayer(client_api: APIClient) -> None:
    """Deux rejeux simultanés : le second ne doit pas inventer une réponse.

    Le cas se produit quand un client relance avant d'avoir reçu la première
    réponse. Rendre un corps fabriqué serait pire que demander de réessayer.
    """
    from shared.infrastructure.idempotence.models import RequeteIdempotente

    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    # La première requête est simulée « en vol » : la trace existe, sans réponse.
    _vendre(client_api, service_id, produit_id, cle="cle-en-vol")
    RequeteIdempotente.objects.filter(cle="cle-en-vol").update(
        statut=RequeteIdempotente.EN_COURS, code_http=None, corps=None
    )

    reponse = _vendre(client_api, service_id, produit_id, cle="cle-en-vol")

    assert reponse.status_code == 409


@pytest.mark.django_db
def test_une_ecriture_sans_cle_est_refusee(client_api: APIClient) -> None:
    """L'obligation est le cœur du dispositif.

    Rendre la clé facultative reviendrait à compter sur le fait qu'aucun client
    n'oublie jamais de l'envoyer — or c'est précisément cet oubli qu'on couvre.
    """
    service_id = ouvrir_service_via_api(client_api)
    produit_id = inscrire_produit_via_api(client_api, prix=1_000)

    reponse = client_api.post(
        f"/api/services/{service_id}/ventes/",
        {"produit_id": produit_id, "quantite": 1, "forme_paiement": "especes"},
        format="json",
        headers={"Idempotency-Key": ""},
    )

    assert reponse.status_code == 400


@pytest.mark.django_db
def test_une_lecture_n_exige_aucune_cle(client_api: APIClient, bar_de_test: str) -> None:
    """Une lecture rejouée ne crée rien : l'exiger serait de la friction gratuite."""
    reponse = client_api.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    assert reponse.status_code == 200


@pytest.mark.django_db
def test_une_ecriture_en_echec_libere_sa_cle(client_api: APIClient) -> None:
    """Le client doit pouvoir corriger et rejouer.

    Retenir un échec condamnerait la vente pour de bon, alors que rien n'a été
    écrit — l'Unit of Work a tout annulé.
    """
    from shared.infrastructure.idempotence.models import RequeteIdempotente

    service_id = ouvrir_service_via_api(client_api)

    echec = _vendre(client_api, service_id, "produit-inexistant", cle="cle-a-liberer")
    assert echec.status_code >= 400

    assert not RequeteIdempotente.objects.filter(cle="cle-a-liberer").exists()

    produit_id = inscrire_produit_via_api(client_api, prix=1_000)
    reprise = _vendre(client_api, service_id, produit_id, cle="cle-a-liberer")

    assert reprise.status_code == 201
