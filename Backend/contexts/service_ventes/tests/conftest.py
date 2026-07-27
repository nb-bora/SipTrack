"""Fixtures et fakes partagés entre tous les tests du contexte Service & Ventes."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from types import TracebackType

from contexts.service_ventes.domain.service import Service
from shared.domain.attribution import Attribution, Capacite
from shared.domain.events import DomainEvent
from shared.domain.money import Montant

INSTANT_TEST = datetime(2026, 7, 24, 17, 0, tzinfo=UTC)


class FakeUnitOfWork:
    """Implémentation fake du port UnitOfWork pour les tests."""

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
    """Implémentation fake du ServiceRepository pour les tests."""

    def __init__(self, service: Service | None = None) -> None:
        self.ajoutes: list[Service] = []
        self.mises_a_jour: list[Service] = []
        self._service = service

    def ajouter(self, service: Service) -> None:
        self.ajoutes.append(service)

    def par_id(self, service_id: str) -> Service | None:
        if self._service is not None:
            return self._service
        return next((s for s in self.ajoutes if s.id == service_id), None)

    def mettre_a_jour(self, service: Service) -> None:
        self.mises_a_jour.append(service)
        # Simule aussi une mise à jour locale
        for i, s in enumerate(self.ajoutes):
            if s.id == service.id:
                self.ajoutes[i] = service
                break


class FakeJournal:
    """Implémentation fake du port Journal pour les tests."""

    def __init__(self) -> None:
        self.appels: list[tuple[tuple[DomainEvent, ...], str]] = []

    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None:
        self.appels.append((tuple(evenements), auteur_id))


class FakeClock:
    """Implémentation fake du port Clock pour les tests."""

    def __init__(self, instant: datetime = INSTANT_TEST) -> None:
        self.instant = instant
        self.appels = 0

    def now(self) -> datetime:
        self.appels += 1
        return self.instant


def creer_service_ouvert(instant: datetime = INSTANT_TEST) -> Service:
    """Crée un service dans l'état OUVERT pour les tests."""
    return Service.ouvrir(
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=instant),
        fond_de_caisse=Montant(10_000),
        horodatage=instant,
    )
