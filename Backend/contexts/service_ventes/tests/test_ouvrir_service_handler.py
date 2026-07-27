"""Test unitaire du cas d'usage — couche application isolée (fakes, sans Django).

Démontre la testabilité de la clean architecture : on branche des doublures en
mémoire sur les ports, sans base ni framework.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import OuvrirServiceCommand
from contexts.service_ventes.application.use_cases.ouvrir_service import (
    OuvrirServiceHandler,
)
from contexts.service_ventes.domain.events import ServiceOuvert
from contexts.service_ventes.tests.conftest import (
    INSTANT_TEST,
    FakeClock,
    FakeJournal,
    FakeServiceRepository,
    FakeUnitOfWork,
)


def _handler() -> tuple[
    OuvrirServiceHandler, FakeUnitOfWork, FakeServiceRepository, FakeJournal, FakeClock
]:
    uow = FakeUnitOfWork()
    services = FakeServiceRepository()
    journal = FakeJournal()
    clock = FakeClock(INSTANT_TEST)
    handler = OuvrirServiceHandler(uow=uow, services=services, journal=journal, clock=clock)
    return handler, uow, services, journal, clock


def _commande() -> OuvrirServiceCommand:
    return OuvrirServiceCommand(
        bar_id="bar1", auteur_id="u1", capacite="operatrice", fond_de_caisse=10_000
    )


def test_le_service_est_ajoute_au_repository_et_le_dto_est_renvoye() -> None:
    handler, _uow, services, _journal, _clock = _handler()

    dto = handler.executer(_commande())

    assert len(services.ajoutes) == 1
    assert dto.statut == "ouvert"
    assert dto.fond_de_caisse == 10_000


def test_un_seul_horodatage_est_utilise_pour_tout_l_acte() -> None:
    handler, _uow, services, _journal, clock = _handler()

    handler.executer(_commande())

    service = services.ajoutes[0]
    assert clock.appels == 1
    assert service.ouvert_le == INSTANT_TEST
    assert service.responsable.horodatage == INSTANT_TEST


def test_les_evenements_sont_journalises_avec_le_bon_auteur_puis_purges() -> None:
    handler, _uow, services, journal, _clock = _handler()

    handler.executer(_commande())

    assert len(journal.appels) == 1
    evenements, auteur_id = journal.appels[0]
    assert auteur_id == "u1"
    assert len(evenements) == 1
    assert isinstance(evenements[0], ServiceOuvert)
    # Après journalisation, l'agrégat ne conserve plus d'événements non publiés.
    assert services.ajoutes[0].evenements_non_publies() == ()


def test_la_transaction_est_validee_en_cas_de_succes() -> None:
    handler, uow, _services, _journal, _clock = _handler()

    handler.executer(_commande())

    assert uow.committed is True
    assert uow.rolled_back is False
