"""Test unitaire du cas d'usage EnregistrerVente — couche application isolée (fakes)."""

from __future__ import annotations

from datetime import datetime

import pytest

from contexts.service_ventes.application.dto import EnregistrerVenteCommand
from contexts.service_ventes.application.use_cases.enregistrer_vente import (
    EnregistrerVenteHandler,
)
from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.enums import StatutService
from contexts.service_ventes.domain.events import VenteEnregistree
from contexts.service_ventes.domain.exceptions import (
    AdditionDejaCloturee,
    AdditionIntrouvable,
    ServiceIntrouvable,
    ServiceNonOuvert,
)
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.tests.conftest import (
    FakeAdditionRepository,
    FakeClock,
    FakeJournal,
    FakeServiceRepository,
    FakeUnitOfWork,
    FakeVenteRepository,
    creer_service_ouvert,
)
from shared.domain.attribution import Attribution, Capacite
from shared.domain.money import Montant

_INSTANT = datetime(2026, 7, 24, 18, 30)


def _service_cloture() -> Service:
    return Service(
        id="svc-clos",
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=_INSTANT),
        fond_de_caisse=Montant(10_000),
        statut=StatutService.CLOTURE,
        ouvert_le=_INSTANT,
    )


def _commande(service_id: str, addition_id: str | None = None) -> EnregistrerVenteCommand:
    return EnregistrerVenteCommand(
        service_id=service_id,
        auteur_id="u1",
        produit_id="33export",
        quantite=2,
        prix_unitaire=650,
        forme_paiement="especes",
        addition_id=addition_id,
    )


def _handler(
    service: Service | None,
    additions: list[Addition] | None = None,
) -> tuple[EnregistrerVenteHandler, FakeUnitOfWork, FakeVenteRepository, FakeJournal]:
    uow = FakeUnitOfWork()
    ventes = FakeVenteRepository()
    journal = FakeJournal()
    handler = EnregistrerVenteHandler(
        uow=uow,
        services=FakeServiceRepository(service),
        ventes=ventes,
        additions=FakeAdditionRepository(additions),
        journal=journal,
        clock=FakeClock(_INSTANT),
    )
    return handler, uow, ventes, journal


def test_la_vente_est_persistee_journalisee_purgee_et_commitee() -> None:
    service = creer_service_ouvert(_INSTANT)
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


def _addition_ouverte(service_id: str) -> Addition:
    return Addition.ouvrir(
        service_id=service_id,
        table_numero=5,
        horodatage=_INSTANT,
        auteur_id="u1",
    )


def test_une_vente_peut_etre_rattachee_a_une_addition_ouverte() -> None:
    service = creer_service_ouvert(_INSTANT)
    addition = _addition_ouverte(service.id)
    handler, uow, ventes, journal = _handler(service, [addition])

    dto = handler.executer(_commande(service.id, addition.id))

    assert dto.addition_id == addition.id
    assert ventes.ajoutes[0].addition_id == addition.id
    evenements, _auteur_id = journal.appels[0]
    evenement = evenements[0]
    assert isinstance(evenement, VenteEnregistree)
    # Le rattachement doit être visible dans le journal, pas seulement en base.
    assert evenement.addition_id == addition.id
    assert uow.committed is True


def test_une_vente_sans_addition_reste_possible() -> None:
    """Encaissement mixte : une consommation au comptoir ne passe par aucune table."""
    service = creer_service_ouvert(_INSTANT)
    handler, uow, ventes, _journal = _handler(service)

    dto = handler.executer(_commande(service.id))

    assert dto.addition_id is None
    assert ventes.ajoutes[0].addition_id is None
    assert uow.committed is True


def test_une_addition_introuvable_leve_addition_introuvable() -> None:
    service = creer_service_ouvert(_INSTANT)
    handler, _uow, ventes, _journal = _handler(service)
    commande = _commande(service.id, "add-inexistante")

    with pytest.raises(AdditionIntrouvable):
        handler.executer(commande)

    assert ventes.ajoutes == []


def test_une_addition_d_un_autre_service_leve_addition_introuvable() -> None:
    service = creer_service_ouvert(_INSTANT)
    addition_ailleurs = _addition_ouverte("svc-autre")
    handler, _uow, ventes, _journal = _handler(service, [addition_ailleurs])
    commande = _commande(service.id, addition_ailleurs.id)

    with pytest.raises(AdditionIntrouvable):
        handler.executer(commande)

    assert ventes.ajoutes == []


def test_une_addition_deja_reglee_refuse_la_vente() -> None:
    service = creer_service_ouvert(_INSTANT)
    addition = _addition_ouverte(service.id)
    addition.regler(auteur_id="u1", horodatage=_INSTANT)
    handler, uow, ventes, _journal = _handler(service, [addition])
    commande = _commande(service.id, addition.id)

    with pytest.raises(AdditionDejaCloturee):
        handler.executer(commande)

    assert ventes.ajoutes == []
    assert uow.committed is False
