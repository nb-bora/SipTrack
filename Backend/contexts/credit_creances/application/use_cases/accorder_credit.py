"""Cas d'usage : ouvrir une créance au nom d'un client.

Appelé quand une consommation part en crédit. Sans lui, l'addition se réglerait
sans qu'aucun argent n'entre et sans que personne ne doive rien : la
consommation s'évaporerait du décompte.
"""

from __future__ import annotations

from contexts.credit_creances.application.dto import AccorderCreditCommand, CreditDTO
from contexts.credit_creances.domain.credit import Credit
from contexts.credit_creances.domain.exceptions import (
    ClientIntrouvable,
    CreditDejaOuvertPourCetteAddition,
)
from contexts.credit_creances.domain.repositories import ClientRepository, CreditRepository
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork
from shared.domain.money import Montant


class AccorderCreditHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        clients: ClientRepository,
        credits: CreditRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._clients = clients
        self._credits = credits
        self._journal = journal
        self._clock = clock

    def executer(self, commande: AccorderCreditCommand) -> CreditDTO:
        with self._uow:
            if self._clients.par_id(commande.client_id) is None:
                raise ClientIntrouvable(commande.client_id)

            # Deux créances pour une même consommation feraient payer deux fois.
            if self._credits.par_addition(commande.addition_id) is not None:
                raise CreditDejaOuvertPourCetteAddition(commande.addition_id)

            credit = Credit.accorder(
                client_id=commande.client_id,
                service_id=commande.service_id,
                addition_id=commande.addition_id,
                montant=Montant(commande.montant),
                horodatage=self._clock.now(),
                auteur_id=commande.auteur_id,
            )
            self._credits.ajouter(credit)
            self._journal.enregistrer(credit.evenements_non_publies(), auteur_id=commande.auteur_id)
            credit.purger_evenements()
            self._uow.commit()
            return CreditDTO.depuis(credit, rembourse=0)
