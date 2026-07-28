"""Test unitaire du cas d'usage VerserRecette — couche application isolée."""

from __future__ import annotations

from datetime import datetime

import pytest

from contexts.service_ventes.application.dto import VerserRecetteCommand
from contexts.service_ventes.application.use_cases.verser_recette import VerserRecetteHandler
from contexts.service_ventes.domain.enums import StatutService
from contexts.service_ventes.domain.events import EcartConstate, RecetteVersee
from contexts.service_ventes.domain.exceptions import (
    RecetteDejaVersee,
    ServiceIntrouvable,
    ServiceNonOuvert,
)
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.domain.versement import Versement
from contexts.service_ventes.tests.conftest import (
    FakeClock,
    FakeJournal,
    FakeServiceRepository,
    FakeUnitOfWork,
    creer_service_ouvert,
)
from shared.domain.attribution import Attribution, Capacite
from shared.domain.money import Montant

_INSTANT = datetime(2026, 7, 28, 23, 30)
_SERVEUSE = "serveuse1"


class FakeVersementRepository:
    def __init__(self, deja_verse: bool = False) -> None:
        self.ajoutes: list[Versement] = []
        self._deja_verse = deja_verse

    def ajouter(self, versement: Versement) -> None:
        self.ajoutes.append(versement)

    def existe_pour(self, *, service_id: str, serveuse_id: str) -> bool:
        return self._deja_verse or any(
            v.service_id == service_id and v.serveuse_id == serveuse_id for v in self.ajoutes
        )


class FakePaiementsEncaisses:
    def __init__(self, especes: int) -> None:
        self._especes = especes

    def ajouter(self, paiement: object) -> None: ...

    def total_encaisse(self, addition_id: str) -> int:
        return 0

    def especes_encaissees_par(self, *, service_id: str, auteur_id: str) -> int:
        return self._especes


def _service_cloture() -> Service:
    return Service(
        id="svc-clos",
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=_INSTANT),
        fond_de_caisse=Montant(10_000),
        statut=StatutService.CLOTURE,
        ouvert_le=_INSTANT,
    )


def _handler(
    service: Service | None,
    *,
    especes: int = 0,
    deja_verse: bool = False,
) -> tuple[VerserRecetteHandler, FakeUnitOfWork, FakeVersementRepository, FakeJournal]:
    uow = FakeUnitOfWork()
    versements = FakeVersementRepository(deja_verse)
    journal = FakeJournal()
    handler = VerserRecetteHandler(
        uow=uow,
        services=FakeServiceRepository(service),
        versements=versements,
        paiements=FakePaiementsEncaisses(especes),
        journal=journal,
        clock=FakeClock(_INSTANT),
    )
    return handler, uow, versements, journal


def _commande(service_id: str, montant: int) -> VerserRecetteCommand:
    return VerserRecetteCommand(service_id=service_id, serveuse_id=_SERVEUSE, montant=montant)


def test_l_attendu_vient_des_especes_encaissees_par_la_serveuse() -> None:
    service = creer_service_ouvert(_INSTANT)
    handler, uow, versements, journal = _handler(service, especes=2_000)

    dto = handler.executer(_commande(service.id, 2_000))

    assert dto.attendu == 2_000
    assert dto.ecart == 0
    assert len(versements.ajoutes) == 1
    evenements, auteur = journal.appels[0]
    assert auteur == _SERVEUSE
    assert [type(e) for e in evenements] == [RecetteVersee]
    assert uow.committed is True


def test_un_ecart_part_au_journal_avec_le_versement() -> None:
    service = creer_service_ouvert(_INSTANT)
    handler, _uow, _versements, journal = _handler(service, especes=2_000)

    dto = handler.executer(_commande(service.id, 1_800))

    assert dto.ecart == -200
    evenements, _auteur = journal.appels[0]
    assert [type(e) for e in evenements] == [RecetteVersee, EcartConstate]


def test_verser_deux_fois_est_refuse() -> None:
    service = creer_service_ouvert(_INSTANT)
    handler, uow, versements, _journal = _handler(service, especes=1_000, deja_verse=True)
    commande = _commande(service.id, 1_000)

    with pytest.raises(RecetteDejaVersee):
        handler.executer(commande)

    assert versements.ajoutes == []
    assert uow.committed is False


def test_un_service_introuvable_leve_l_erreur() -> None:
    handler, _uow, _versements, _journal = _handler(None)
    commande = _commande("inconnu", 1_000)

    with pytest.raises(ServiceIntrouvable):
        handler.executer(commande)


def test_un_service_cloture_refuse_le_versement() -> None:
    handler, _uow, versements, _journal = _handler(_service_cloture(), especes=1_000)
    commande = _commande("svc-clos", 1_000)

    with pytest.raises(ServiceNonOuvert):
        handler.executer(commande)

    assert versements.ajoutes == []
