"""Cas d'usage : enregistrer une vente sur un service ouvert.

Coordonne deux agrégats (cohérence eventual, cf. ADR-0004) : on charge le Service
pour vérifier qu'il est ouvert, puis on crée l'agrégat Vente, on le persiste et on
journalise ses événements — le tout dans une unité de travail atomique.

Le prix n'est **jamais** celui qu'on nous envoie : il est lu au catalogue, qui
seul fait autorité. Sans cela, la personne qui saisit déciderait de ce que la
consommation a valu.
"""

from __future__ import annotations

from contexts.service_ventes.application.dto import EnregistrerVenteCommand, VenteDTO
from contexts.service_ventes.application.ports import TarifDuProduit
from contexts.service_ventes.domain.enums import FormePaiement, StatutService
from contexts.service_ventes.domain.exceptions import (
    AdditionIntrouvable,
    ServiceIntrouvable,
    ServiceNonOuvert,
)
from contexts.service_ventes.domain.repositories import (
    AdditionRepository,
    ServiceRepository,
    VenteRepository,
)
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
        additions: AdditionRepository,
        tarifs: TarifDuProduit,
        journal: Journal,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._services = services
        self._ventes = ventes
        self._additions = additions
        self._tarifs = tarifs
        self._journal = journal
        self._clock = clock

    def executer(self, commande: EnregistrerVenteCommand) -> VenteDTO:
        with self._uow:
            service = self._services.par_id(commande.service_id)
            if service is None:
                raise ServiceIntrouvable(commande.service_id)
            if service.statut is not StatutService.OUVERT:
                raise ServiceNonOuvert(commande.service_id)

            if commande.addition_id is not None:
                self._verifier_addition(commande.addition_id, service_id=service.id)

            # Le prix vient du catalogue, et il est copié sur la vente : une
            # vente d'hier garde le prix d'hier même si le tarif change ce soir.
            article = self._tarifs.prix_de(
                produit_id=commande.produit_id,
                bar_id=service.bar_id,
            )

            vente = Vente.enregistrer(
                service_id=service.id,
                produit_id=commande.produit_id,
                quantite=commande.quantite,
                prix_unitaire=Montant(article.prix_unitaire),
                forme_paiement=FormePaiement(commande.forme_paiement),
                horodatage=self._clock.now(),
                auteur_id=commande.auteur_id,
                addition_id=commande.addition_id,
            )
            self._ventes.ajouter(vente)
            self._journal.enregistrer(
                vente.evenements_non_publies(),
                auteur_id=commande.auteur_id,
            )
            vente.purger_evenements()
            self._uow.commit()
            return VenteDTO.depuis(vente)

    def _verifier_addition(self, addition_id: str, *, service_id: str) -> None:
        """L'addition doit exister, appartenir à ce service et être ouverte."""
        addition = self._additions.par_id(addition_id)
        # Une addition d'un autre service est, du point de vue de ce service,
        # inexistante : on ne révèle pas son existence.
        if addition is None or addition.service_id != service_id:
            raise AdditionIntrouvable(addition_id)
        addition.accepter_consommation()
