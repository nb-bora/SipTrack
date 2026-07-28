"""Agrégat racine : Remboursement.

Un versement du client sur sa dette. Agrégat distinct du crédit, exactement
comme le Paiement est distinct de l'Addition : chaque remboursement est un Fait
autonome, horodaté et attribué, qu'aucune écriture ultérieure ne peut fondre
dans un total.
"""

from __future__ import annotations

from datetime import datetime

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.domain.money import Montant

from .events import RemboursementRecu


class Remboursement:
    def __init__(
        self,
        *,
        id: str,
        credit_id: str,
        client_id: str,
        montant: Montant,
        horodatage: datetime,
        auteur_id: str,
    ) -> None:
        self.id = id
        self.credit_id = credit_id
        self.client_id = client_id
        self.montant = montant
        self.horodatage = horodatage
        self.auteur_id = auteur_id
        self._evenements: list[DomainEvent] = []

    @classmethod
    def encaisser(
        cls,
        *,
        credit_id: str,
        client_id: str,
        montant: Montant,
        horodatage: datetime,
        auteur_id: str,
    ) -> Remboursement:
        remboursement = cls(
            id=new_id(),
            credit_id=credit_id,
            client_id=client_id,
            montant=montant,
            horodatage=horodatage,
            auteur_id=auteur_id,
        )
        remboursement._enregistrer(
            RemboursementRecu(
                remboursement_id=remboursement.id,
                credit_id=credit_id,
                client_id=client_id,
                montant=montant.valeur,
                auteur_id=auteur_id,
            )
        )
        return remboursement

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
