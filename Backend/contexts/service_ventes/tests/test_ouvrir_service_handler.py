"""Test unitaire du cas d'usage — couche application isolée (fakes, sans Django).

Démontre la testabilité de la clean architecture : on branche des doublures en
mémoire sur les ports, sans base ni framework.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from types import TracebackType

from contexts.service_ventes.application.dto import OuvrirServiceCommand
from contexts.service_ventes.application.use_cases.ouvrir_service import (
    OuvrirServiceHandler,
)
from contexts.service_ventes.domain.events import ServiceOuvert
from contexts.service_ventes.domain.service import Service
from shared.domain.events import DomainEvent

_INSTANT = datetime(2026, 7, 24, 17, 0, tzinfo=UTC)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rolled_back = True

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakeServiceRepository:
    def __init__(self) -> None:
        self.ajoutes: list[Service] = []

    def ajouter(self, service: Service) -> None:
        self.ajoutes.append(service)

    def par_id(self, service_id: str) -> Service | None:
        return next((s for s in self.ajoutes if s.id == service_id), None)


class FakeJournal:
    def __init__(self) -> None:
        self.appels: list[tuple[tuple[DomainEvent, ...], str]] = []

    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None:
        self.appels.append((tuple(evenements), auteur_id))


class FakeClock:
    def __init__(self, instant: datetime) -> None:
        self.instant = instant
        self.appels = 0

    def now(self) -> datetime:
        self.appels += 1
        return self.instant


def _handler() -> tuple[
    OuvrirServiceHandler, FakeUnitOfWork, FakeServiceRepository, FakeJournal, FakeClock
]:
    uow = FakeUnitOfWork()
    services = FakeServiceRepository()
    journal = FakeJournal()
    clock = FakeClock(_INSTANT)
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
    assert service.ouvert_le == _INSTANT
    assert service.responsable.horodatage == _INSTANT


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
