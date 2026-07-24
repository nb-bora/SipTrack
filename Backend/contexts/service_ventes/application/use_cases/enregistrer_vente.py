"""Cas d'usage : enregistrer une vente sur un service ouvert.

Coordonne deux agrégats (cohérence eventual, cf. ADR-0004) : on charge le Service
pour vérifier qu'il est ouvert, puis on crée l'agrégat Vente, on le persiste et on
journalise ses événements — le tout dans une unité de travail atomique.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import EnregistrerVenteCommand, VenteDTO
from contexts.service_ventes.domain.enums import FormePaiement, StatutService
from contexts.service_ventes.domain.exceptions import ServiceIntrouvable, ServiceNonOuvert
from contexts.service_ventes.domain.repositories import ServiceRepository, VenteRepository
from contexts.service_ventes.domain.vente import Vente
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork
from shared.domain.money import Montant


class EnregistrerVenteHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        services: ServiceRepository,
        ventes: VenteRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._services = services
        self._ventes = ventes
        self._journal = journal
        self._clock = clock

    def executer(self, commande: EnregistrerVenteCommand) -> VenteDTO:
        with self._uow:
            service = self._services.par_id(commande.service_id)
            if service is None:
                raise ServiceIntrouvable(commande.service_id)
            if service.statut is not StatutService.OUVERT:
                raise ServiceNonOuvert(commande.service_id)

            vente = Vente.enregistrer(
                service_id=service.id,
                produit_id=commande.produit_id,
                quantite=commande.quantite,
                prix_unitaire=Montant(commande.prix_unitaire),
                forme_paiement=FormePaiement(commande.forme_paiement),
                horodatage=self._clock.now(),
                auteur_id=commande.auteur_id,
            )
            self._ventes.ajouter(vente)
            self._journal.enregistrer(
                vente.evenements_non_publies(),
                auteur_id=commande.auteur_id,
            )
            vente.purger_evenements()
            self._uow.commit()
            return VenteDTO.depuis(vente)
