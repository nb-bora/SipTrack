"""Le journal est-il réellement inaltérable ?

Ces tests ne vérifient pas une intention mais un comportement : ils tentent
vraiment de réécrire l'histoire, y compris en SQL direct — le scénario contre
lequel un journal d'audit existe.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import DatabaseError, connection, transaction
from rest_framework.test import APIClient

from contexts.service_ventes.tests.conftest import (
    ouvrir_addition_via_api,
    ouvrir_service_via_api,
)
from shared.infrastructure.journal.empreinte import GENESE, calculer_empreinte
from shared.infrastructure.journal.models import JournalInalterable, MouvementModel
from shared.infrastructure.journal.verification import verifier_journal

_HORODATAGE = datetime(2026, 7, 28, 20, 0, tzinfo=UTC)


def _ecrire_mouvement(sequence: int, *, empreinte_precedente: str, type_: str = "FaitTest") -> str:
    """Écrit un Mouvement cohérent et renvoie son empreinte."""
    identifiant = f"mvt-{sequence}"
    donnees = {"valeur": sequence}
    empreinte = calculer_empreinte(
        identifiant=identifiant,
        type_evenement=type_,
        auteur_id="u1",
        donnees=donnees,
        horodatage_saisie=_HORODATAGE,
        sequence=sequence,
        empreinte_precedente=empreinte_precedente,
    )
    MouvementModel.objects.create(
        id=identifiant,
        sequence=sequence,
        type=type_,
        auteur_id="u1",
        donnees=donnees,
        horodatage_saisie=_HORODATAGE,
        empreinte=empreinte,
        empreinte_precedente=empreinte_precedente,
    )
    return empreinte


@pytest.mark.django_db
def test_les_faits_ecrits_par_l_api_forment_une_chaine_verifiable(client_api: APIClient) -> None:
    """Le vrai test d'intégration : ce que l'API écrit doit se vérifier."""
    service_id = ouvrir_service_via_api(client_api)
    addition_id = ouvrir_addition_via_api(client_api, service_id)
    client_api.post(
        f"/api/services/{service_id}/additions/{addition_id}/reglement/",
        format="json",
    )

    mouvements = list(MouvementModel.objects.order_by("sequence"))

    assert len(mouvements) == 3
    assert [m.sequence for m in mouvements] == [1, 2, 3]
    assert mouvements[0].empreinte_precedente == GENESE
    assert mouvements[1].empreinte_precedente == mouvements[0].empreinte
    assert mouvements[2].empreinte_precedente == mouvements[1].empreinte
    assert verifier_journal() == []


@pytest.mark.django_db
def test_modifier_un_mouvement_est_refuse_par_la_base() -> None:
    """En SQL direct : ni l'ORM ni l'application ne sont dans la boucle."""
    _ecrire_mouvement(1, empreinte_precedente=GENESE)

    with (
        pytest.raises(DatabaseError, match="append-only"),
        transaction.atomic(),
        connection.cursor() as curseur,
    ):
        curseur.execute("UPDATE journal_mouvement SET auteur_id = 'quelqu-un-d-autre'")


@pytest.mark.django_db
def test_supprimer_un_mouvement_est_refuse_par_la_base() -> None:
    _ecrire_mouvement(1, empreinte_precedente=GENESE)

    with (
        pytest.raises(DatabaseError, match="append-only"),
        transaction.atomic(),
        connection.cursor() as curseur,
    ):
        curseur.execute("DELETE FROM journal_mouvement")


@pytest.mark.django_db
def test_tronquer_le_journal_est_refuse_par_la_base() -> None:
    """TRUNCATE contourne les déclencheurs de ligne : il a le sien."""
    _ecrire_mouvement(1, empreinte_precedente=GENESE)

    with (
        pytest.raises(DatabaseError, match="append-only"),
        transaction.atomic(),
        connection.cursor() as curseur,
    ):
        curseur.execute("TRUNCATE journal_mouvement")


@pytest.mark.django_db
def test_modifier_un_mouvement_via_l_orm_est_refuse() -> None:
    _ecrire_mouvement(1, empreinte_precedente=GENESE)
    mouvement = MouvementModel.objects.get(pk="mvt-1")
    mouvement.auteur_id = "quelqu-un-d-autre"

    with pytest.raises(JournalInalterable):
        mouvement.save()


@pytest.mark.django_db
def test_supprimer_un_mouvement_via_l_orm_est_refuse() -> None:
    _ecrire_mouvement(1, empreinte_precedente=GENESE)
    mouvement = MouvementModel.objects.get(pk="mvt-1")

    with pytest.raises(JournalInalterable):
        mouvement.delete()


@pytest.mark.django_db
def test_un_journal_sain_ne_presente_aucune_anomalie() -> None:
    empreinte = _ecrire_mouvement(1, empreinte_precedente=GENESE)
    empreinte = _ecrire_mouvement(2, empreinte_precedente=empreinte)
    _ecrire_mouvement(3, empreinte_precedente=empreinte)

    assert verifier_journal() == []


@pytest.mark.django_db
def test_un_mouvement_dont_le_contenu_ne_correspond_pas_est_detecte() -> None:
    """Le scénario réel : quelqu'un a contourné la garde et réécrit une ligne."""
    empreinte = _ecrire_mouvement(1, empreinte_precedente=GENESE)
    _ecrire_mouvement(2, empreinte_precedente=empreinte)

    # On désactive la garde le temps de simuler l'altération.
    with connection.cursor() as curseur:
        curseur.execute("ALTER TABLE journal_mouvement DISABLE TRIGGER USER")
        curseur.execute("UPDATE journal_mouvement SET auteur_id = 'faussaire' WHERE sequence = 1")
        curseur.execute("ALTER TABLE journal_mouvement ENABLE TRIGGER USER")

    anomalies = verifier_journal()

    assert len(anomalies) == 1
    assert anomalies[0].sequence == 1
    assert "altéré" in anomalies[0].motif


@pytest.mark.django_db
def test_une_chaine_rompue_est_detectee() -> None:
    """Un Mouvement inséré avec une empreinte précédente inventée."""
    _ecrire_mouvement(1, empreinte_precedente=GENESE)
    _ecrire_mouvement(2, empreinte_precedente="f" * 64)

    anomalies = verifier_journal()

    assert len(anomalies) == 1
    assert anomalies[0].sequence == 2
    assert "chaîne est rompue" in anomalies[0].motif


@pytest.mark.django_db
def test_un_trou_dans_la_sequence_est_detecte() -> None:
    """Le cas d'une suppression réussie malgré tout : le compte n'y est plus."""
    empreinte = _ecrire_mouvement(1, empreinte_precedente=GENESE)
    empreinte_2 = calculer_empreinte(
        identifiant="mvt-3",
        type_evenement="FaitTest",
        auteur_id="u1",
        donnees={"valeur": 3},
        horodatage_saisie=_HORODATAGE,
        sequence=3,
        empreinte_precedente=empreinte,
    )
    MouvementModel.objects.create(
        id="mvt-3",
        sequence=3,
        type="FaitTest",
        auteur_id="u1",
        donnees={"valeur": 3},
        horodatage_saisie=_HORODATAGE,
        empreinte=empreinte_2,
        empreinte_precedente=empreinte,
    )

    anomalies = verifier_journal()

    assert len(anomalies) == 1
    assert "séquence 3" in anomalies[0].motif
