"""Test unitaire du cas d'usage CloturerService — couche application isolée (fakes)."""

from __future__ import annotations

from datetime import datetime

import pytest

from contexts.service_ventes.application.dto import CloturerServiceCommand
from contexts.service_ventes.application.use_cases.cloturer_service import (
    CloturerServiceHandler,
)
from contexts.service_ventes.domain.enums import StatutService
from contexts.service_ventes.domain.events import ServiceCloture
from contexts.service_ventes.domain.exceptions import (
    ServiceDejaCloture,
    ServiceIntrouvable,
)
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.tests.conftest import (
    FakeClock,
    FakeJournal,
    FakeServiceRepository,
    FakeUnitOfWork,
    creer_service_ouvert,
)
from shared.domain.attribution import Attribution, Capacite
from shared.domain.money import Montant

_INSTANT = datetime(2026, 7, 24, 19, 0)


def _service_cloture() -> Service:
    return Service(
        id="svc-clos",
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=_INSTANT),
        fond_de_caisse=Montant(10_000),
        statut=StatutService.CLOTURE,
        ouvert_le=_INSTANT,
    )


def _commande(service_id: str) -> CloturerServiceCommand:
    return CloturerServiceCommand(
        service_id=service_id,
        auteur_id="u1",
    )


def _handler(
    service: Service | None,
) -> tuple[CloturerServiceHandler, FakeUnitOfWork, FakeServiceRepository, FakeJournal]:
    uow = FakeUnitOfWork()
    services = FakeServiceRepository(service)
    journal = FakeJournal()
    handler = CloturerServiceHandler(
        uow=uow,
        services=services,
        journal=journal,
        clock=FakeClock(_INSTANT),
    )
    return handler, uow, services, journal


def test_le_service_est_mis_a_jour_et_le_dto_est_renvoye() -> None:
    service = creer_service_ouvert(_INSTANT)
    handler, _uow, services, _journal = _handler(service)

    dto = handler.executer(_commande(service.id))

    assert len(services.mises_a_jour) == 1
    assert dto.statut == "cloture"
    assert dto.clos_le is not None


def test_les_evenements_sont_journalises_avec_le_bon_auteur_puis_purges() -> None:
    service = creer_service_ouvert(_INSTANT)
    service.purger_evenements()  # Le service renvoyé par le repository serait déjà purgé en prod
    handler, _uow, services, journal = _handler(service)

    handler.executer(_commande(service.id))

    assert len(journal.appels) == 1
    evenements, auteur_id = journal.appels[0]
    assert auteur_id == "u1"
    assert len(evenements) == 1
    assert isinstance(evenements[0], ServiceCloture)
    # Après journalisation, l'agrégat ne conserve plus d'événements non publiés.
    assert services.mises_a_jour[0].evenements_non_publies() == ()


def test_la_transaction_est_validee_en_cas_de_succes() -> None:
    service = creer_service_ouvert(_INSTANT)
    handler, uow, _services, _journal = _handler(service)

    handler.executer(_commande(service.id))

    assert uow.committed is True
    assert uow.rolled_back is False


def test_un_service_introuvable_leve_service_introuvable() -> None:
    handler, _uow, _services, _journal = _handler(None)
    commande = _commande("inconnu")

    with pytest.raises(ServiceIntrouvable):
        handler.executer(commande)


def test_un_service_deja_cloture_leve_service_deja_cloture() -> None:
    service = _service_cloture()
    handler, _uow, _services, _journal = _handler(service)
    commande = _commande(service.id)

    with pytest.raises(ServiceDejaCloture):
        handler.executer(commande)
