"""Cas d'usage : clôturer un service.

Charge le Service, l'applique à la clôture, le persiste, journalise l'événement,
le tout dans une unité de travail atomique.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import CloturerServiceCommand, ServiceDTO
from contexts.service_ventes.domain.exceptions import ServiceIntrouvable
from contexts.service_ventes.domain.repositories import ServiceRepository
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork


class CloturerServiceHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        services: ServiceRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._services = services
        self._journal = journal
        self._clock = clock

    def executer(self, commande: CloturerServiceCommand) -> ServiceDTO:
        with self._uow:
            service = self._services.par_id(commande.service_id)
            if service is None:
                raise ServiceIntrouvable(commande.service_id)

            service.cloturer(
                auteur_id=commande.auteur_id,
                horodatage=self._clock.now(),
            )
            self._services.mettre_a_jour(service)
            self._journal.enregistrer(
                service.evenements_non_publies(),
                auteur_id=commande.auteur_id,
            )
            service.purger_evenements()
            self._uow.commit()
            return ServiceDTO.depuis(service)
