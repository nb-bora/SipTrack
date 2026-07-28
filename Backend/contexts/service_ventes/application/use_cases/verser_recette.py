"""Cas d'usage : une serveuse verse sa recette.

Première des deux réconciliations emboîtées (modèle métier §9) : on confronte ce
qu'elle a encaissé en espèces à ce qu'elle remet. C'est le contrôle **quotidien**
de l'outil — celui qui attrape « a saisi une vente et gardé le cash ».

Ce qu'il n'attrape pas, et qu'il faut assumer : la vente jamais saisie. Seul un
inventaire physique la révèle.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import VersementDTO, VerserRecetteCommand
from contexts.service_ventes.domain.enums import StatutService
from contexts.service_ventes.domain.exceptions import (
    RecetteDejaVersee,
    ServiceIntrouvable,
    ServiceNonOuvert,
)
from contexts.service_ventes.domain.repositories import (
    PaiementRepository,
    ServiceRepository,
    VersementRepository,
)
from contexts.service_ventes.domain.versement import Versement
from shared.application.clock import Clock
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork
from shared.domain.money import Montant


class VerserRecetteHandler:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        services: ServiceRepository,
        versements: VersementRepository,
        paiements: PaiementRepository,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._services = services
        self._versements = versements
        self._paiements = paiements
        self._journal = journal
        self._clock = clock

    def executer(self, commande: VerserRecetteCommand) -> VersementDTO:
        with self._uow:
            service = self._services.par_id(commande.service_id)
            if service is None:
                raise ServiceIntrouvable(commande.service_id)
            if service.statut is not StatutService.OUVERT:
                raise ServiceNonOuvert(commande.service_id)

            # La serveuse verse pour elle-même : `serveuse_id` vient du jeton.
            if self._versements.existe_pour(
                service_id=service.id,
                serveuse_id=commande.serveuse_id,
            ):
                raise RecetteDejaVersee(service.id, commande.serveuse_id)

            attendu = self._paiements.especes_encaissees_par(
                service_id=service.id,
                auteur_id=commande.serveuse_id,
            )

            versement = Versement.remettre(
                service_id=service.id,
                serveuse_id=commande.serveuse_id,
                attendu=Montant(attendu),
                verse=Montant(commande.montant),
                horodatage=self._clock.now(),
            )
            self._versements.ajouter(versement)
            self._journal.enregistrer(
                versement.evenements_non_publies(),
                auteur_id=commande.serveuse_id,
            )
            versement.purger_evenements()
            self._uow.commit()
            return VersementDTO.depuis(versement)
