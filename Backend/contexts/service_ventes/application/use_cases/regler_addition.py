"""Cas d'usage : régler une addition.

Orchestre le domaine : charge l'addition, la régle, la persiste, journalise
ses événements, le tout dans une unité de travail atomique.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import AdditionDTO, ReglementAdditionCommand
from contexts.service_ventes.domain.exceptions import AdditionIntrouvable, AdditionNonSoldee
from contexts.service_ventes.domain.repositories import (
    AdditionRepository,
    PaiementRepository,
    VenteRepository,
)
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork


class ReglementAdditionHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        additions: AdditionRepository,
        paiements: PaiementRepository,
        ventes: VenteRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._additions = additions
        self._paiements = paiements
        self._ventes = ventes
        self._journal = journal
        self._clock = clock

    def executer(self, commande: ReglementAdditionCommand) -> AdditionDTO:
        with self._uow:
            addition = self._additions.par_id(commande.addition_id)
            if addition is None:
                raise AdditionIntrouvable(commande.addition_id)

            if addition.service_id != commande.service_id:
                raise AdditionIntrouvable(commande.addition_id)

            # Clore une addition sans avoir encaissé ferait disparaître la
            # créance : le reste dû doit être à zéro.
            reste = self._ventes.total_addition(addition.id) - self._paiements.total_encaisse(
                addition.id
            )
            if reste > 0:
                raise AdditionNonSoldee(addition.id, reste)

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
