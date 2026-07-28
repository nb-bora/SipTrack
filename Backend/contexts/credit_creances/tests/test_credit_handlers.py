"""Les cas d'usage du crédit, sans base de données."""

from __future__ import annotations

import pytest

from contexts.credit_creances.application.dto import (
    AccorderCreditCommand,
    CreerClientCommand,
    EnregistrerRemboursementCommand,
)
from contexts.credit_creances.application.use_cases.accorder_credit import (
    AccorderCreditHandler,
)
from contexts.credit_creances.application.use_cases.creer_client import CreerClientHandler
from contexts.credit_creances.application.use_cases.enregistrer_remboursement import (
    EnregistrerRemboursementHandler,
)
from contexts.credit_creances.domain.client import Client
from contexts.credit_creances.domain.credit import Credit
from contexts.credit_creances.domain.enums import StatutCredit
from contexts.credit_creances.domain.events import CreditSolde, RemboursementRecu
from contexts.credit_creances.domain.exceptions import (
    ClientIntrouvable,
    CreditDejaOuvertPourCetteAddition,
    CreditDejaSolde,
    CreditIntrouvable,
    RemboursementSuperieurAuReste,
)
from contexts.credit_creances.tests.conftest import (
    INSTANT_TEST,
    FakeClientRepository,
    FakeClock,
    FakeCreditRepository,
    FakeJournal,
    FakeRemboursementRepository,
    FakeUnitOfWork,
)
from shared.domain.money import Montant

_CLIENT = Client(id="cli1", bar_id="bar1", nom="Jean")


def _credit_existant(montant: int = 5_000, statut: StatutCredit = StatutCredit.NE) -> Credit:
    return Credit(
        id="cre1",
        client_id="cli1",
        service_id="svc1",
        addition_id="add1",
        montant=Montant(montant),
        statut=statut,
        ne_le=INSTANT_TEST,
    )


# --- Enregistrer un client ---------------------------------------------------


def test_un_client_est_cree_une_fois() -> None:
    uow = FakeUnitOfWork()
    clients = FakeClientRepository()
    handler = CreerClientHandler(uow=uow, clients=clients)

    dto = handler.executer(CreerClientCommand(bar_id="bar1", nom="Jean"))

    assert dto.nom == "Jean"
    assert len(clients.ajoutes) == 1
    assert uow.committed is True


def test_un_nom_deja_connu_renvoie_le_meme_client() -> None:
    """Sinon une même personne porterait deux dettes séparées."""
    clients = FakeClientRepository([_CLIENT])
    handler = CreerClientHandler(uow=FakeUnitOfWork(), clients=clients)

    dto = handler.executer(CreerClientCommand(bar_id="bar1", nom="Jean"))

    assert dto.id == _CLIENT.id
    assert clients.ajoutes == []


# --- Accorder un crédit ------------------------------------------------------


def _accorder(
    *,
    clients: FakeClientRepository | None = None,
    credits: FakeCreditRepository | None = None,
) -> tuple[AccorderCreditHandler, FakeUnitOfWork, FakeCreditRepository, FakeJournal]:
    uow = FakeUnitOfWork()
    depot_credits = credits or FakeCreditRepository()
    journal = FakeJournal()
    handler = AccorderCreditHandler(
        uow=uow,
        clients=clients or FakeClientRepository([_CLIENT]),
        credits=depot_credits,
        journal=journal,
        clock=FakeClock(),
    )
    return handler, uow, depot_credits, journal


def _commande_credit(montant: int = 5_000) -> AccorderCreditCommand:
    return AccorderCreditCommand(
        client_id="cli1",
        service_id="svc1",
        addition_id="add1",
        montant=montant,
        auteur_id="serveuse1",
    )


def test_une_creance_nait_au_nom_du_client() -> None:
    handler, uow, credits, journal = _accorder()

    dto = handler.executer(_commande_credit(5_000))

    assert dto.montant == 5_000
    assert dto.rembourse == 0
    assert dto.reste == 5_000
    assert dto.statut == "ne"
    assert len(credits.ajoutes) == 1
    assert uow.committed is True
    _, auteur = journal.appels[0]
    assert auteur == "serveuse1"


def test_un_credit_pour_un_client_inconnu_est_refuse() -> None:
    handler, uow, credits, _journal = _accorder(clients=FakeClientRepository([]))
    commande = _commande_credit()

    with pytest.raises(ClientIntrouvable):
        handler.executer(commande)

    assert credits.ajoutes == []
    assert uow.committed is False


def test_une_addition_n_engendre_qu_une_seule_creance() -> None:
    """Deux créances pour une même consommation feraient payer deux fois."""
    handler, uow, credits, _journal = _accorder(credits=FakeCreditRepository([_credit_existant()]))
    commande = _commande_credit()

    with pytest.raises(CreditDejaOuvertPourCetteAddition):
        handler.executer(commande)

    assert credits.ajoutes == []
    assert uow.committed is False


# --- Rembourser --------------------------------------------------------------


def _rembourser(
    credit: Credit | None,
    *,
    deja_rembourse: int = 0,
) -> tuple[
    EnregistrerRemboursementHandler,
    FakeUnitOfWork,
    FakeCreditRepository,
    FakeRemboursementRepository,
    FakeJournal,
]:
    uow = FakeUnitOfWork()
    credits = FakeCreditRepository([credit] if credit is not None else [])
    remboursements = FakeRemboursementRepository(
        {credit.id: deja_rembourse} if credit is not None else {}
    )
    journal = FakeJournal()
    handler = EnregistrerRemboursementHandler(
        uow=uow,
        credits=credits,
        remboursements=remboursements,
        journal=journal,
        clock=FakeClock(),
    )
    return handler, uow, credits, remboursements, journal


def _commande_remboursement(montant: int) -> EnregistrerRemboursementCommand:
    return EnregistrerRemboursementCommand(credit_id="cre1", montant=montant, auteur_id="gerante1")


def test_un_remboursement_partiel_laisse_la_dette_ouverte() -> None:
    credit = _credit_existant(5_000)
    handler, uow, credits, remboursements, journal = _rembourser(credit)

    dto = handler.executer(_commande_remboursement(2_000))

    assert dto.rembourse == 2_000
    assert dto.reste == 3_000
    assert dto.statut == "ne"
    assert len(remboursements.ajoutes) == 1
    assert credits.mis_a_jour == []  # la dette n'est pas éteinte
    assert [type(e) for e in journal.evenements()] == [RemboursementRecu]
    assert uow.committed is True


def test_le_dernier_franc_eteint_la_dette_de_lui_meme() -> None:
    """Le solde est une conséquence, jamais une déclaration."""
    credit = _credit_existant(5_000)
    handler, _uow, credits, _remb, journal = _rembourser(credit, deja_rembourse=3_000)

    dto = handler.executer(_commande_remboursement(2_000))

    assert dto.reste == 0
    assert dto.statut == "solde"
    assert len(credits.mis_a_jour) == 1
    assert [type(e) for e in journal.evenements()] == [RemboursementRecu, CreditSolde]


def test_rembourser_plus_que_le_reste_est_refuse() -> None:
    credit = _credit_existant(5_000)
    handler, uow, _credits, remboursements, _journal = _rembourser(credit, deja_rembourse=4_000)
    commande = _commande_remboursement(1_500)

    with pytest.raises(RemboursementSuperieurAuReste) as erreur:
        handler.executer(commande)

    assert erreur.value.reste == 1_000
    assert remboursements.ajoutes == []
    assert uow.committed is False


def test_rembourser_un_credit_deja_solde_est_refuse() -> None:
    credit = _credit_existant(5_000, statut=StatutCredit.SOLDE)
    handler, uow, _credits, remboursements, _journal = _rembourser(credit, deja_rembourse=5_000)
    commande = _commande_remboursement(500)

    with pytest.raises(CreditDejaSolde):
        handler.executer(commande)

    assert remboursements.ajoutes == []
    assert uow.committed is False


def test_rembourser_un_credit_inexistant_leve_l_erreur() -> None:
    handler, _uow, _credits, _remb, _journal = _rembourser(None)
    commande = _commande_remboursement(500)

    with pytest.raises(CreditIntrouvable):
        handler.executer(commande)
