"""Test unitaire du cas d'usage EnregistrerPaiement — couche application isolée."""

from __future__ import annotations

from datetime import datetime

import pytest

from contexts.service_ventes.application.dto import EnregistrerPaiementCommand
from contexts.service_ventes.application.use_cases.enregistrer_paiement import (
    EnregistrerPaiementHandler,
)
from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.enums import StatutAddition
from contexts.service_ventes.domain.events import AdditionReglee, PaiementRecu
from contexts.service_ventes.domain.exceptions import (
    AdditionDejaCloturee,
    AdditionIntrouvable,
    PaiementSuperieurAuReste,
)
from contexts.service_ventes.tests.conftest import (
    FakeAdditionRepository,
    FakeClock,
    FakeJournal,
    FakePaiementRepository,
    FakeUnitOfWork,
    FakeVenteRepository,
)

_INSTANT = datetime(2026, 7, 28, 21, 30)
_SERVICE = "svc1"


def _addition_ouverte() -> Addition:
    addition = Addition.ouvrir(
        service_id=_SERVICE,
        table_numero=5,
        horodatage=_INSTANT,
        auteur_id="u1",
    )
    addition.purger_evenements()
    return addition


def _commande(addition_id: str, montant: int) -> EnregistrerPaiementCommand:
    return EnregistrerPaiementCommand(
        service_id=_SERVICE,
        addition_id=addition_id,
        auteur_id="u1",
        montant=montant,
        forme_paiement="especes",
    )


def _handler(
    addition: Addition | None,
    *,
    du: int = 0,
    deja_encaisse: int = 0,
) -> tuple[
    EnregistrerPaiementHandler,
    FakeUnitOfWork,
    FakePaiementRepository,
    FakeAdditionRepository,
    FakeJournal,
]:
    uow = FakeUnitOfWork()
    additions = FakeAdditionRepository([addition] if addition is not None else [])
    identifiant = addition.id if addition is not None else "inconnue"
    paiements = FakePaiementRepository({identifiant: deja_encaisse})
    journal = FakeJournal()
    handler = EnregistrerPaiementHandler(
        uow=uow,
        additions=additions,
        paiements=paiements,
        ventes=FakeVenteRepository({identifiant: du}),
        journal=journal,
        clock=FakeClock(_INSTANT),
    )
    return handler, uow, paiements, additions, journal


def test_un_paiement_partiel_est_encaisse_sans_regler_l_addition() -> None:
    addition = _addition_ouverte()
    handler, uow, paiements, additions, journal = _handler(addition, du=2_000)

    dto = handler.executer(_commande(addition.id, 500))

    assert dto.montant == 500
    assert dto.reste_a_payer == 1_500
    assert len(paiements.ajoutes) == 1
    assert addition.statut is StatutAddition.OUVERTE
    assert additions.mises_a_jour == []
    evenements, _auteur = journal.appels[0]
    assert len(evenements) == 1
    assert isinstance(evenements[0], PaiementRecu)
    assert uow.committed is True


def test_payer_le_solde_regle_l_addition_dans_la_meme_transaction() -> None:
    addition = _addition_ouverte()
    handler, uow, _paiements, additions, journal = _handler(addition, du=2_000, deja_encaisse=1_500)

    dto = handler.executer(_commande(addition.id, 500))

    assert dto.reste_a_payer == 0
    assert addition.statut is StatutAddition.REGLEE
    assert len(additions.mises_a_jour) == 1
    evenements, _auteur = journal.appels[0]
    # Les deux Faits partent ensemble : l'encaissement et le règlement.
    assert [type(e) for e in evenements] == [PaiementRecu, AdditionReglee]
    assert uow.committed is True


def test_payer_plus_que_le_reste_est_refuse() -> None:
    addition = _addition_ouverte()
    handler, uow, paiements, _additions, _journal = _handler(addition, du=1_000)
    commande = _commande(addition.id, 1_500)

    with pytest.raises(PaiementSuperieurAuReste) as erreur:
        handler.executer(commande)

    assert erreur.value.reste == 1_000
    assert paiements.ajoutes == []
    assert uow.committed is False


def test_payer_une_addition_close_est_refuse() -> None:
    addition = _addition_ouverte()
    addition.regler(auteur_id="u1", horodatage=_INSTANT)
    addition.purger_evenements()
    handler, _uow, paiements, _additions, _journal = _handler(addition, du=1_000)
    commande = _commande(addition.id, 500)

    with pytest.raises(AdditionDejaCloturee):
        handler.executer(commande)

    assert paiements.ajoutes == []


def test_payer_une_addition_introuvable_est_refuse() -> None:
    handler, _uow, paiements, _additions, _journal = _handler(None)
    commande = _commande("inconnue", 500)

    with pytest.raises(AdditionIntrouvable):
        handler.executer(commande)

    assert paiements.ajoutes == []


def test_payer_une_addition_d_un_autre_service_est_refuse() -> None:
    addition = Addition.ouvrir(
        service_id="svc-ailleurs",
        table_numero=5,
        horodatage=_INSTANT,
        auteur_id="u1",
    )
    handler, _uow, paiements, _additions, _journal = _handler(addition, du=1_000)
    commande = _commande(addition.id, 500)

    with pytest.raises(AdditionIntrouvable):
        handler.executer(commande)

    assert paiements.ajoutes == []
