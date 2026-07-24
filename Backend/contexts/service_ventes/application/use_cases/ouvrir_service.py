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
            # Un seul horodatage pour tout l'acte : l'attribution et l'ouverture
            # du service partagent le même instant (cohérence + testabilité).
            horodatage = self._clock.now()
            responsable = Attribution(
                auteur_id=commande.auteur_id,
                capacite=Capacite(commande.capacite),
                horodatage=horodatage,
            )
            service = Service.ouvrir(
                bar_id=commande.bar_id,
                responsable=responsable,
                fond_de_caisse=Montant(commande.fond_de_caisse),
                horodatage=horodatage,
            )
            self._services.ajouter(service)
            self._journal.enregistrer(
                service.evenements_non_publies(),
                auteur_id=commande.auteur_id,
            )
            service.purger_evenements()
            self._uow.commit()
            return ServiceDTO.depuis(service)
