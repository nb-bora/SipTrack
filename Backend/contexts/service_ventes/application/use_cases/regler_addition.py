"""Cas d'usage : régler une addition.

Orchestre le domaine : charge l'addition, la régle, la persiste, journalise
ses événements, le tout dans une unité de travail atomique.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import AdditionDTO, ReglementAdditionCommand
from contexts.service_ventes.domain.exceptions import AdditionIntrouvable
from contexts.service_ventes.domain.repositories import AdditionRepository
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork


class ReglementAdditionHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        additions: AdditionRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._additions = additions
        self._journal = journal
        self._clock = clock

    def executer(self, commande: ReglementAdditionCommand) -> AdditionDTO:
        with self._uow:
            addition = self._additions.par_id(commande.addition_id)
            if addition is None:
                raise AdditionIntrouvable(commande.addition_id)

            addition.regler(
                auteur_id=commande.auteur_id,
                horodatage=self._clock.now(),
            )
            self._additions.mettre_a_jour(addition)
            self._journal.enregistrer(
                addition.evenements_non_publies(),
                auteur_id=commande.auteur_id,
            )
            addition.purger_evenements()
            self._uow.commit()
            return AdditionDTO.depuis(addition)
