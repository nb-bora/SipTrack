"""Un compte plateforme voit tout, n'écrit nulle part, et laisse une trace.

Le privilège de consultation est la seule dérogation au cloisonnement posé par
`test_autorisation.py`. Il n'est tenable qu'à trois conditions, chacune éprouvée
ici :

1. il ne donne **aucun** droit d'écrire, dans aucun bar ;
2. chaque consultation exercée à ce titre est **inscrite** ;
3. le propriétaire du bar peut **la lire**.

Sans (1), le journal métier cesse d'être opposable : en litige, la défense
deviendrait « un compte de la plateforme a pu écrire ce mouvement ». Sans (2) et
(3), « je peux tout voir sans que vous le sachiez » — ce qui ne se défend pas.
"""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient


def _client_de(utilisateur: Any) -> APIClient:
    from rest_framework.authtoken.models import Token

    jeton, _ = Token.objects.get_or_create(user=utilisateur)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {jeton.key}")
    return client


@pytest.fixture
def support(db: None, django_user_model: Any) -> Any:
    """Un compte plateforme habilité à consulter n'importe quel bar."""
    from contexts.gouvernance_acces.domain.enums import CapacitePlateforme
    from contexts.gouvernance_acces.infrastructure.django_app.models import (
        AdministrateurPlateformeModel,
    )

    personne = django_user_model.objects.create_user(username="support")
    AdministrateurPlateformeModel.objects.create(
        id="admin-support",
        user=personne,
        capacites=sorted(CapacitePlateforme.toutes()),
    )
    return personne


@pytest.fixture
def bar_d_un_client(db: None, django_user_model: Any) -> tuple[str, Any]:
    """Un bar tenu par quelqu'un d'autre, avec un service ouvert."""
    patronne = django_user_model.objects.create_user(username="patronne-cliente")
    client = _client_de(patronne)
    bar = client.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()
    identifiant = bar["id"]
    assert isinstance(identifiant, str)
    return identifiant, patronne


# ---------------------------------------------------------------------------
# Ce que le privilège permet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_le_support_consulte_le_bar_d_un_client(
    support: Any, bar_d_un_client: tuple[str, Any]
) -> None:
    """Sans compte dans ce bar, et pourtant autorisé à lire — c'est le besoin."""
    bar_id, _ = bar_d_un_client

    reponse = _client_de(support).get(f"/api/bars/{bar_id}/encours/", format="json")

    assert reponse.status_code == 200


# ---------------------------------------------------------------------------
# Ce que le privilège ne permet pas — le cœur du sujet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_le_support_ne_peut_pas_ouvrir_un_service(
    support: Any, bar_d_un_client: tuple[str, Any]
) -> None:
    """Lire ne donne pas d'écrire. Le journal doit rester opposable."""
    bar_id, _ = bar_d_un_client

    reponse = _client_de(support).post(
        "/api/services/",
        {"bar_id": bar_id, "fond_de_caisse": 50_000},
        format="json",
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_le_support_ne_peut_ecrire_dans_aucun_contexte(
    support: Any, bar_d_un_client: tuple[str, Any]
) -> None:
    """Un seul contexte oublié suffirait à rouvrir la porte.

    Ce test existe pour que l'ajout d'une capacité d'écriture aux comptes
    plateforme — la tentation qui reviendra — échoue immédiatement.
    """
    bar_id, _ = bar_d_un_client
    client = _client_de(support)

    ecritures = [
        ("/api/produits/", {"bar_id": bar_id, "nom": "Biere", "prix": 1_000}),
        ("/api/clients/", {"bar_id": bar_id, "nom": "Client"}),
        (
            "/api/inventaire/produits/",
            {"bar_id": bar_id, "nom": "Casier", "quantite_initiale": 10},
        ),
    ]
    for chemin, corps in ecritures:
        reponse = client.post(chemin, corps, format="json")
        assert reponse.status_code == 403, f"POST {chemin} a répondu {reponse.status_code}"


@pytest.mark.django_db
def test_un_compte_plateforme_suspendu_ne_lit_plus(
    support: Any, bar_d_un_client: tuple[str, Any]
) -> None:
    """Retirer l'habilitation doit produire son effet sans redéploiement."""
    from contexts.gouvernance_acces.infrastructure.django_app.models import (
        AdministrateurPlateformeModel,
    )

    bar_id, _ = bar_d_un_client
    AdministrateurPlateformeModel.objects.filter(user=support).update(actif=False)

    reponse = _client_de(support).get(f"/api/bars/{bar_id}/encours/", format="json")

    assert reponse.status_code == 403


# ---------------------------------------------------------------------------
# La contrepartie : la trace
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_consultation_par_privilege_est_tracee(
    support: Any, bar_d_un_client: tuple[str, Any]
) -> None:
    """Sans cette trace, le privilège ne serait pas défendable."""
    from contexts.gouvernance_acces.infrastructure.django_app.models import (
        AccesPlateformeModel,
    )

    bar_id, _ = bar_d_un_client
    _client_de(support).get(f"/api/bars/{bar_id}/encours/", format="json")

    traces = AccesPlateformeModel.objects.filter(bar_id=bar_id)
    assert traces.count() == 1
    trace = traces.get()
    assert trace.administrateur_id == str(support.pk)
    assert trace.operation


@pytest.mark.django_db
def test_une_lecture_ordinaire_ne_laisse_aucune_trace(
    client_api: APIClient, bar_de_test: str
) -> None:
    """Le journal des accès répond à « qui d'extérieur a regardé mon bar ».

    Y verser les lectures ordinaires le rendrait illisible — et ferait payer une
    écriture à chaque consultation d'une gérante dans son propre établissement.
    """
    from contexts.gouvernance_acces.infrastructure.django_app.models import (
        AccesPlateformeModel,
    )

    client_api.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    assert AccesPlateformeModel.objects.count() == 0


@pytest.mark.django_db
def test_le_proprietaire_voit_qui_a_consulte_son_bar(
    support: Any, bar_d_un_client: tuple[str, Any]
) -> None:
    """La trace ne vaut que si elle est lisible par l'intéressé."""
    bar_id, patronne = bar_d_un_client
    _client_de(support).get(f"/api/bars/{bar_id}/encours/", format="json")

    reponse = _client_de(patronne).get(f"/api/bars/{bar_id}/acces/", format="json")

    assert reponse.status_code == 200
    acces = reponse.json()
    assert len(acces) == 1
    assert acces[0]["administrateur_id"] == str(support.pk)


@pytest.mark.django_db
def test_les_acces_d_un_bar_ne_sont_pas_publics(
    support: Any, bar_d_un_client: tuple[str, Any], django_user_model: Any
) -> None:
    """Qui consulte quoi renseigne sur l'activité du support et des clients."""
    bar_id, _ = bar_d_un_client
    curieux = django_user_model.objects.create_user(username="curieux")

    reponse = _client_de(curieux).get(f"/api/bars/{bar_id}/acces/", format="json")

    assert reponse.status_code == 403


# ---------------------------------------------------------------------------
# Garde-fou durable
# ---------------------------------------------------------------------------


def test_les_capacites_plateforme_n_autorisent_aucune_ecriture_metier() -> None:
    """Les deux axes ne doivent jamais se recouper.

    Si un nom se retrouvait dans les deux énumérations, une capacité plateforme
    pourrait satisfaire un contrôle d'exploitation par simple coïncidence de
    chaîne — et la garantie « lire, jamais écrire » tomberait sans qu'aucun test
    fonctionnel ne s'en aperçoive.
    """
    from contexts.gouvernance_acces.domain.enums import (
        CapaciteAtomique,
        CapacitePlateforme,
    )

    communes = CapacitePlateforme.toutes() & CapaciteAtomique.toutes()
    assert communes == frozenset(), f"Capacités présentes des deux côtés : {communes}"
