"""Cas d'usage : ouvrir une addition sur un service ouvert.

Orchestre le domaine : construit l'agrégat, le persiste, journalise ses
événements, le tout dans une unité de travail atomique.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import AdditionDTO, OuvrirAdditionCommand
from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.exceptions import ServiceIntrouvable, ServiceNonOuvert
from contexts.service_ventes.domain.repositories import AdditionRepository, ServiceRepository
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork


class OuvrirAdditionHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        services: ServiceRepository,
        additions: AdditionRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._services = services
        self._additions = additions
        self._journal = journal
        self._clock = clock

    def executer(self, commande: OuvrirAdditionCommand) -> AdditionDTO:
        with self._uow:
            service = self._services.par_id(commande.service_id)
            if service is None:
                raise ServiceIntrouvable(commande.service_id)
            if not service.statut.value == "ouvert":
                raise ServiceNonOuvert(commande.service_id)

            addition = Addition.ouvrir(
                service_id=service.id,
                table_numero=commande.table_numero,
                horodatage=self._clock.now(),
                auteur_id=commande.auteur_id,
            )
            self._additions.ajouter(addition)
            self._journal.enregistrer(
                addition.evenements_non_publies(),
                auteur_id=commande.auteur_id,
            )
            addition.purger_evenements()
            self._uow.commit()
            return AdditionDTO.depuis(addition)
