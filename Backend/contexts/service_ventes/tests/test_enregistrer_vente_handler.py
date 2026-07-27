"""Test unitaire du cas d'usage EnregistrerVente — couche application isolée (fakes)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from types import TracebackType

import pytest

from contexts.service_ventes.application.dto import EnregistrerVenteCommand
from contexts.service_ventes.application.use_cases.enregistrer_vente import (
    EnregistrerVenteHandler,
)
from contexts.service_ventes.domain.enums import StatutService
from contexts.service_ventes.domain.events import VenteEnregistree
from contexts.service_ventes.domain.exceptions import ServiceIntrouvable, ServiceNonOuvert
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.domain.vente import Vente
from shared.domain.attribution import Attribution, Capacite
from shared.domain.events import DomainEvent
from shared.domain.money import Montant

_INSTANT = datetime(2026, 7, 24, 18, 30, tzinfo=UTC)


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
    def __init__(self, service: Service | None) -> None:
        self._service = service

    def ajouter(self, service: Service) -> None:  # pragma: no cover - non utilisé ici
        raise NotImplementedError

    def par_id(self, service_id: str) -> Service | None:
        return self._service

    def mettre_a_jour(self, service: Service) -> None:  # pragma: no cover - non utilisé ici
        raise NotImplementedError


class FakeVenteRepository:
    def __init__(self) -> None:
        self.ajoutes: list[Vente] = []

    def ajouter(self, vente: Vente) -> None:
        self.ajoutes.append(vente)


class FakeJournal:
    def __init__(self) -> None:
        self.appels: list[tuple[tuple[DomainEvent, ...], str]] = []

    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None:
        self.appels.append((tuple(evenements), auteur_id))


class FakeClock:
    def __init__(self, instant: datetime) -> None:
        self.instant = instant

    def now(self) -> datetime:
        return self.instant


def _service_ouvert() -> Service:
    return Service.ouvrir(
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=_INSTANT),
        fond_de_caisse=Montant(10_000),
        horodatage=_INSTANT,
    )


def _service_cloture() -> Service:
    return Service(
        id="svc-clos",
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=_INSTANT),
        fond_de_caisse=Montant(10_000),
        statut=StatutService.CLOTURE,
        ouvert_le=_INSTANT,
    )


def _commande(service_id: str) -> EnregistrerVenteCommand:
    return EnregistrerVenteCommand(
        service_id=service_id,
        auteur_id="u1",
        produit_id="33export",
        quantite=2,
        prix_unitaire=650,
        forme_paiement="especes",
    )


def _handler(
    service: Service | None,
) -> tuple[EnregistrerVenteHandler, FakeUnitOfWork, FakeVenteRepository, FakeJournal]:
    uow = FakeUnitOfWork()
    ventes = FakeVenteRepository()
    journal = FakeJournal()
    handler = EnregistrerVenteHandler(
        uow=uow,
        services=FakeServiceRepository(service),
        ventes=ventes,
        journal=journal,
        clock=FakeClock(_INSTANT),
    )
    return handler, uow, ventes, journal


def test_la_vente_est_persistee_journalisee_purgee_et_commitee() -> None:
    service = _service_ouvert()
    handler, uow, ventes, journal = _handler(service)

    dto = handler.executer(_commande(service.id))

    assert len(ventes.ajoutes) == 1
    assert dto.montant_total == 1_300
    assert dto.service_id == service.id
    assert len(journal.appels) == 1
    evenements, auteur_id = journal.appels[0]
    assert auteur_id == "u1"
    assert isinstance(evenements[0], VenteEnregistree)
    assert ventes.ajoutes[0].evenements_non_publies() == ()
    assert uow.committed is True


def test_un_service_introuvable_leve_service_introuvable() -> None:
    handler, _uow, _ventes, _journal = _handler(None)
    commande = _commande("inconnu")

    with pytest.raises(ServiceIntrouvable):
        handler.executer(commande)


def test_un_service_non_ouvert_leve_service_non_ouvert() -> None:
    service = _service_cloture()
    handler, _uow, _ventes, _journal = _handler(service)
    commande = _commande(service.id)

    with pytest.raises(ServiceNonOuvert):
        handler.executer(commande)
