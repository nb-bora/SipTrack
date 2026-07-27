"""Tests du handler ReglementAdditionHandler — avec fakes (mémoire)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contexts.service_ventes.application.dto import (
    AdditionDTO,
    ReglementAdditionCommand,
)
from contexts.service_ventes.application.use_cases.regler_addition import (
    ReglementAdditionHandler,
)
from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.enums import StatutAddition
from contexts.service_ventes.domain.exceptions import (
    AdditionDejaCloturee,
    AdditionIntrouvable,
)
from contexts.service_ventes.tests.conftest import (
    FakeAdditionRepository,
    FakeJournal,
    FakeUnitOfWork,
    SystemClockFake,
)

_HORODATAGE = datetime(2026, 7, 28, 10, 0, tzinfo=UTC)
_HORODATAGE_REGLEMENT = datetime(2026, 7, 28, 22, 30, tzinfo=UTC)


def test_regler_une_addition_la_met_a_jour_et_la_journalise() -> None:
    addition = Addition.ouvrir(
        service_id="svc1",
        table_numero=5,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )
    additions_repo = FakeAdditionRepository([addition])
    journal = FakeJournal()
    clock = SystemClockFake(_HORODATAGE_REGLEMENT)
    uow = FakeUnitOfWork()

    handler = ReglementAdditionHandler(
        uow=uow,
        additions=additions_repo,
        journal=journal,
        clock=clock,
    )
    cmd = ReglementAdditionCommand(
        service_id="svc1",
        addition_id=addition.id,
        auteur_id="u1",
    )

    dto = handler.executer(cmd)

    assert isinstance(dto, AdditionDTO)
    assert dto.statut == "reglee"
    assert dto.ferme_le is not None
    addition_en_repo = additions_repo.par_id(addition.id)
    assert addition_en_repo is not None
    assert addition_en_repo.statut is StatutAddition.REGLEE


def test_l_evenement_addition_reglee_est_journalise() -> None:
    addition = Addition.ouvrir(
        service_id="svc1",
        table_numero=5,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )
    addition.purger_evenements()
    additions_repo = FakeAdditionRepository([addition])
    journal = FakeJournal()
    clock = SystemClockFake(_HORODATAGE_REGLEMENT)
    uow = FakeUnitOfWork()

    handler = ReglementAdditionHandler(
        uow=uow,
        additions=additions_repo,
        journal=journal,
        clock=clock,
    )
    cmd = ReglementAdditionCommand(
        service_id="svc1",
        addition_id=addition.id,
        auteur_id="u1",
    )

    handler.executer(cmd)

    assert len(journal.mouvements) == 1
    mouvement = journal.mouvements[0]
    assert mouvement["type"] == "AdditionReglee"
    assert mouvement["addition_id"] == addition.id


def test_regler_une_addition_introuvable_leve_l_erreur() -> None:
    additions_repo = FakeAdditionRepository([])
    journal = FakeJournal()
    clock = SystemClockFake(_HORODATAGE_REGLEMENT)
    uow = FakeUnitOfWork()

    handler = ReglementAdditionHandler(
        uow=uow,
        additions=additions_repo,
        journal=journal,
        clock=clock,
    )
    cmd = ReglementAdditionCommand(
        service_id="svc1",
        addition_id="add-inexistante",
        auteur_id="u1",
    )

    with pytest.raises(AdditionIntrouvable):
        handler.executer(cmd)


def test_regler_une_addition_deja_reglee_leve_l_erreur() -> None:
    addition = Addition(
        id="add1",
        service_id="svc1",
        table_numero=5,
        statut=StatutAddition.REGLEE,
        ouvert_le=_HORODATAGE,
        ferme_le=_HORODATAGE_REGLEMENT,
    )
    additions_repo = FakeAdditionRepository([addition])
    journal = FakeJournal()
    clock = SystemClockFake(_HORODATAGE_REGLEMENT)
    uow = FakeUnitOfWork()

    handler = ReglementAdditionHandler(
        uow=uow,
        additions=additions_repo,
        journal=journal,
        clock=clock,
    )
    cmd = ReglementAdditionCommand(
        service_id="svc1",
        addition_id="add1",
        auteur_id="u1",
    )

    with pytest.raises(AdditionDejaCloturee):
        handler.executer(cmd)
