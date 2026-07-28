"""Cas d'usage : encaisser un remboursement sur une créance.

Le solde d'un crédit est une **conséquence**, pas une déclaration : quand le
cumul des remboursements atteint le montant dû, la dette s'éteint d'elle-même.
Exactement comme une addition se règle quand ses paiements la couvrent.
"""

from __future__ import annotations

from contexts.credit_creances.application.dto import (
    CreditDTO,
    EnregistrerRemboursementCommand,
)
from contexts.credit_creances.domain.enums import StatutCredit
from contexts.credit_creances.domain.exceptions import (
    CreditDejaSolde,
    CreditIntrouvable,
    RemboursementSuperieurAuReste,
)
from contexts.credit_creances.domain.remboursement import Remboursement
from contexts.credit_creances.domain.repositories import (
    CreditRepository,
    RemboursementRepository,
)
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork
from shared.domain.money import Montant


class EnregistrerRemboursementHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        credits: CreditRepository,
        remboursements: RemboursementRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._credits = credits
        self._remboursements = remboursements
        self._journal = journal
        self._clock = clock

    def executer(self, commande: EnregistrerRemboursementCommand) -> CreditDTO:
        with self._uow:
            credit = self._credits.par_id(commande.credit_id)
            if credit is None:
                raise CreditIntrouvable(commande.credit_id)
            if credit.statut is StatutCredit.SOLDE:
                raise CreditDejaSolde(credit.id)

            deja_rembourse = self._remboursements.total_rembourse(credit.id)
            reste = credit.montant.valeur - deja_rembourse
            if commande.montant > reste:
                raise RemboursementSuperieurAuReste(credit.id, reste)

            remboursement = Remboursement.encaisser(
                credit_id=credit.id,
                client_id=credit.client_id,
                montant=Montant(commande.montant),
                horodatage=self._clock.now(),
                auteur_id=commande.auteur_id,
            )
            self._remboursements.ajouter(remboursement)

            evenements = list(remboursement.evenements_non_publies())

            # Dette éteinte : le crédit se solde de lui-même, même transaction.
            if commande.montant == reste:
                credit.solder(auteur_id=commande.auteur_id)
                self._credits.mettre_a_jour(credit)
                evenements.extend(credit.evenements_non_publies())

            self._journal.enregistrer(evenements, auteur_id=commande.auteur_id)
            remboursement.purger_evenements()
            credit.purger_evenements()
            self._uow.commit()
            return CreditDTO.depuis(credit, rembourse=deja_rembourse + commande.montant)
