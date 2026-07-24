"""Agrégat racine : Vente.

Une vente enregistrée pendant un service. Petit agrégat (cf. ADR-0004) qui
référence son service par identifiant. Aucune dépendance à Django.
"""

from __future__ import annotations

from datetime import datetime

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.domain.money import Montant

from .enums import FormePaiement
from .events import VenteEnregistree


class Vente:
    def __init__(
        self,
        *,
        id: str,
        service_id: str,
        produit_id: str,
        quantite: int,
        prix_unitaire: Montant,
        forme_paiement: FormePaiement,
        horodatage: datetime,
    ) -> None:
        self.id = id
        self.service_id = service_id
        self.produit_id = produit_id
        self.quantite = quantite
        self.prix_unitaire = prix_unitaire
        self.forme_paiement = forme_paiement
        self.horodatage = horodatage
        self._evenements: list[DomainEvent] = []

    @property
    def montant_total(self) -> Montant:
        return Montant(self.prix_unitaire.montant * self.quantite, self.prix_unitaire.devise)

    @classmethod
    def enregistrer(
        cls,
        *,
        service_id: str,
        produit_id: str,
        quantite: int,
        prix_unitaire: Montant,
        forme_paiement: FormePaiement,
        horodatage: datetime,
        auteur_id: str,
    ) -> Vente:
        if quantite <= 0:
            raise ValueError("La quantité vendue doit être strictement positive.")
        vente = cls(
            id=new_id(),
            service_id=service_id,
            produit_id=produit_id,
            quantite=quantite,
            prix_unitaire=prix_unitaire,
            forme_paiement=forme_paiement,
            horodatage=horodatage,
        )
        vente._enregistrer(
            VenteEnregistree(
                vente_id=vente.id,
                service_id=service_id,
                produit_id=produit_id,
                quantite=quantite,
                prix_unitaire=prix_unitaire.montant,
                montant_total=vente.montant_total.montant,
                forme_paiement=forme_paiement.value,
                auteur_id=auteur_id,
            )
        )
        return vente

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
