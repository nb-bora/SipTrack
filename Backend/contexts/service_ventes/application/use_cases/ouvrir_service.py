"""Cas d'usage : ouvrir un service.

Orchestre le domaine : construit l'agrégat, le persiste, journalise ses
événements, le tout dans une unité de travail atomique.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import OuvrirServiceCommand, ServiceDTO
from contexts.service_ventes.domain.repositories import ServiceRepository
from contexts.service_ventes.domain.service import Service
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork
from shared.domain.attribution import Attribution, Capacite
from shared.domain.money import Montant


class OuvrirServiceHandler:
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

    def executer(self, commande: OuvrirServiceCommand) -> ServiceDTO:
        with self._uow:
            responsable = Attribution(
                auteur_id=commande.auteur_id,
                capacite=Capacite(commande.capacite),
                horodatage=self._clock.now(),
            )
            service = Service.ouvrir(
                bar_id=commande.bar_id,
                responsable=responsable,
                fond_de_caisse=Montant(commande.fond_de_caisse),
                horodatage=self._clock.now(),
            )
            self._services.ajouter(service)
            self._journal.enregistrer(
                service.evenements_non_publies(),
                auteur_id=commande.auteur_id,
            )
            self._uow.commit()
            return ServiceDTO.depuis(service)
