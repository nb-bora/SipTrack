"""Le domaine du crédit, isolé de toute infrastructure."""

from __future__ import annotations

from contexts.credit_creances.domain.credit import Credit
from contexts.credit_creances.domain.enums import StatutCredit
from contexts.credit_creances.domain.events import (
    CreditAccorde,
    CreditSolde,
    RemboursementRecu,
)
from contexts.credit_creances.domain.remboursement import Remboursement
from contexts.credit_creances.tests.conftest import INSTANT_TEST
from shared.domain.money import Montant


def _credit(montant: int = 5_000) -> Credit:
    return Credit.accorder(
        client_id="cli1",
        service_id="svc1",
        addition_id="add1",
        montant=Montant(montant),
        horodatage=INSTANT_TEST,
        auteur_id="serveuse1",
    )


def test_un_credit_nait_avec_la_dette_entiere() -> None:
    credit = _credit(5_000)

    assert credit.statut is StatutCredit.NE
    assert credit.montant.valeur == 5_000
    assert credit.client_id == "cli1"
    assert credit.addition_id == "add1"

    (evenement,) = credit.evenements_non_publies()
    assert isinstance(evenement, CreditAccorde)
    assert evenement.montant == 5_000
    assert evenement.auteur_id == "serveuse1"


def test_le_credit_ne_porte_pas_ce_qui_a_ete_rembourse() -> None:
    """Un solde stocké est un solde qui finit par mentir : il se recalcule."""
    credit = _credit()

    assert not hasattr(credit, "montant_rembourse")
    assert not hasattr(credit, "reste")


def test_solder_eteint_la_dette_et_produit_un_fait() -> None:
    credit = _credit()
    credit.purger_evenements()

    credit.solder(auteur_id="gerante1")

    assert credit.statut is StatutCredit.SOLDE
    (evenement,) = credit.evenements_non_publies()
    assert isinstance(evenement, CreditSolde)
    assert evenement.credit_id == credit.id
    assert evenement.auteur_id == "gerante1"


def test_un_remboursement_est_un_fait_horodate_et_attribue() -> None:
    """Chaque remboursement reste une ligne : jamais fondu dans un total."""
    remboursement = Remboursement.encaisser(
        credit_id="cre1",
        client_id="cli1",
        montant=Montant(2_000),
        horodatage=INSTANT_TEST,
        auteur_id="serveuse1",
    )

    assert remboursement.montant.valeur == 2_000
    assert remboursement.horodatage == INSTANT_TEST
    assert remboursement.auteur_id == "serveuse1"

    (evenement,) = remboursement.evenements_non_publies()
    assert isinstance(evenement, RemboursementRecu)
    assert evenement.remboursement_id == remboursement.id
    assert evenement.credit_id == "cre1"
    assert evenement.montant == 2_000
