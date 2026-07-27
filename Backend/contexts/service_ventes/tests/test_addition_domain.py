"""Tests du domaine Addition — purs, sans Django."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.enums import StatutAddition
from contexts.service_ventes.domain.events import AdditionOuverte, AdditionReglee
from contexts.service_ventes.domain.exceptions import AdditionDejaCloturee

_HORODATAGE = datetime(2026, 7, 28, 10, 0, tzinfo=UTC)


def test_ouvrir_addition_met_le_statut_a_ouverte() -> None:
    addition = Addition.ouvrir(
        service_id="svc1",
        table_numero=5,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )

    assert addition.statut is StatutAddition.OUVERTE
    assert addition.table_numero == 5
    assert addition.service_id == "svc1"


def test_ouvrir_addition_emet_l_evenement_addition_ouverte() -> None:
    addition = Addition.ouvrir(
        service_id="svc1",
        table_numero=5,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )

    evenements = addition.evenements_non_publies()
    assert len(evenements) == 1
    evenement = evenements[0]
    assert isinstance(evenement, AdditionOuverte)
    assert evenement.addition_id == addition.id
    assert evenement.service_id == "svc1"
    assert evenement.table_numero == 5
    assert evenement.auteur_id == "u1"


def test_purger_les_evenements_vide_la_liste() -> None:
    addition = Addition.ouvrir(
        service_id="svc1",
        table_numero=5,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )
    assert len(addition.evenements_non_publies()) == 1

    addition.purger_evenements()

    assert addition.evenements_non_publies() == ()


def test_regler_addition_met_le_statut_a_reglee() -> None:
    addition = Addition.ouvrir(
        service_id="svc1",
        table_numero=5,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )
    addition.purger_evenements()

    horodatage_reglement = datetime(2026, 7, 28, 22, 30, tzinfo=UTC)
    addition.regler(auteur_id="u1", horodatage=horodatage_reglement)

    assert addition.statut is StatutAddition.REGLEE
    assert addition.ferme_le == horodatage_reglement


def test_regler_addition_emet_l_evenement_addition_reglee() -> None:
    addition = Addition.ouvrir(
        service_id="svc1",
        table_numero=5,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )
    addition.purger_evenements()

    horodatage_reglement = datetime(2026, 7, 28, 22, 30, tzinfo=UTC)
    addition.regler(auteur_id="u1", horodatage=horodatage_reglement)

    evenements = addition.evenements_non_publies()
    assert len(evenements) == 1
    evenement = evenements[0]
    assert isinstance(evenement, AdditionReglee)
    assert evenement.addition_id == addition.id
    assert evenement.service_id == "svc1"
    assert evenement.table_numero == 5
    assert evenement.auteur_id == "u1"


@pytest.mark.parametrize(
    "statut_initial",
    [
        StatutAddition.REGLEE,
        StatutAddition.ABANDONNEE,
    ],
)
def test_regler_une_addition_deja_cloturee_est_interdite(statut_initial: StatutAddition) -> None:
    addition = Addition(
        id="add1",
        service_id="svc1",
        table_numero=5,
        statut=statut_initial,
        ouvert_le=_HORODATAGE,
        ferme_le=_HORODATAGE,
    )

    with pytest.raises(AdditionDejaCloturee):
        addition.regler(auteur_id="u1", horodatage=_HORODATAGE)
