"""Test unitaire du cas d'usage OuvrirAddition — couche application isolée (fakes)."""

from __future__ import annotations

from datetime import datetime

import pytest

from contexts.service_ventes.application.dto import OuvrirAdditionCommand
from contexts.service_ventes.application.use_cases.ouvrir_addition import (
    OuvrirAdditionHandler,
)
from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.events import AdditionOuverte
from contexts.service_ventes.domain.exceptions import (
    ServiceIntrouvable,
    ServiceNonOuvert,
)
from contexts.service_ventes.tests.conftest import (
    INSTANT_TEST,
    FakeClock,
    FakeJournal,
    FakeServiceRepository,
    FakeUnitOfWork,
    creer_service_ouvert,
)

_INSTANT = datetime(2026, 7, 28, 10, 0)


class FakeAdditionRepository:
    def __init__(self) -> None:
        self.ajoutes: list[Addition] = []

    def ajouter(self, addition: Addition) -> None:
        self.ajoutes.append(addition)

    def par_id(self, addition_id: str) -> Addition | None:
        return next((a for a in self.ajoutes if a.id == addition_id), None)


def _handler(
    service_repo: FakeServiceRepository,
) -> tuple[OuvrirAdditionHandler, FakeUnitOfWork, FakeAdditionRepository, FakeJournal]:
    uow = FakeUnitOfWork()
    additions = FakeAdditionRepository()
    journal = FakeJournal()
    handler = OuvrirAdditionHandler(
        uow=uow,
        services=service_repo,
        additions=additions,
        journal=journal,
        clock=FakeClock(_INSTANT),
    )
    return handler, uow, additions, journal


def _commande(service_id: str) -> OuvrirAdditionCommand:
    return OuvrirAdditionCommand(
        service_id=service_id,
        auteur_id="u1",
        table_numero=5,
    )


def test_l_addition_est_ajoutee_et_le_dto_est_renvoye() -> None:
    service = creer_service_ouvert(INSTANT_TEST)
    service_repo = FakeServiceRepository(service)
    handler, _uow, additions, _journal = _handler(service_repo)

    dto = handler.executer(_commande(service.id))

    assert len(additions.ajoutes) == 1
    assert dto.statut == "ouverte"
    assert dto.table_numero == 5


def test_les_evenements_sont_journalises_avec_le_bon_auteur_puis_purges() -> None:
    service = creer_service_ouvert(INSTANT_TEST)
    service.purger_evenements()
    service_repo = FakeServiceRepository(service)
    handler, _uow, additions, journal = _handler(service_repo)

    handler.executer(_commande(service.id))

    assert len(journal.appels) == 1
    evenements, auteur_id = journal.appels[0]
    assert auteur_id == "u1"
    assert len(evenements) == 1
    assert isinstance(evenements[0], AdditionOuverte)
    assert additions.ajoutes[0].evenements_non_publies() == ()


def test_la_transaction_est_validee_en_cas_de_succes() -> None:
    service = creer_service_ouvert(INSTANT_TEST)
    service_repo = FakeServiceRepository(service)
    handler, uow, _additions, _journal = _handler(service_repo)

    handler.executer(_commande(service.id))

    assert uow.committed is True
    assert uow.rolled_back is False


def test_un_service_introuvable_leve_service_introuvable() -> None:
    service_repo = FakeServiceRepository(None)
    handler, _uow, _additions, _journal = _handler(service_repo)
    commande = _commande("inconnu")

    with pytest.raises(ServiceIntrouvable):
        handler.executer(commande)


def test_un_service_non_ouvert_leve_service_non_ouvert() -> None:
    from contexts.service_ventes.domain.enums import StatutService
    from contexts.service_ventes.domain.service import Service
    from shared.domain.attribution import Attribution, Capacite
    from shared.domain.money import Montant

    service = Service(
        id="svc-clos",
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=_INSTANT),
        fond_de_caisse=Montant(10_000),
        statut=StatutService.CLOTURE,
        ouvert_le=_INSTANT,
    )
    service_repo = FakeServiceRepository(service)
    handler, _uow, _additions, _journal = _handler(service_repo)
    commande = _commande(service.id)

    with pytest.raises(ServiceNonOuvert):
        handler.executer(commande)
