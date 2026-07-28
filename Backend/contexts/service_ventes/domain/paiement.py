"""Agrégat racine : Paiement.

Un encaissement sur une addition. Petit agrégat (cf. ADR-0004) qui référence
son addition par identifiant.

Un paiement ne se modifie pas : encaisser moins que prévu ou rendre de la
monnaie sont d'autres Faits, pas la correction de celui-ci.
"""

from __future__ import annotations

from datetime import datetime

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.domain.money import Montant

from .enums import FormePaiement
from .events import PaiementRecu


class Paiement:
    def __init__(
        self,
        *,
        id: str,
        addition_id: str,
        service_id: str,
        montant: Montant,
        forme_paiement: FormePaiement,
        horodatage: datetime,
    ) -> None:
        self.id = id
        self.addition_id = addition_id
        self.service_id = service_id
        self.montant = montant
        self.forme_paiement = forme_paiement
        self.horodatage = horodatage
        self._evenements: list[DomainEvent] = []

    @classmethod
    def encaisser(
        cls,
        *,
        addition_id: str,
        service_id: str,
        montant: Montant,
        forme_paiement: FormePaiement,
        horodatage: datetime,
        auteur_id: str,
    ) -> Paiement:
        if montant.valeur <= 0:
            raise ValueError("Un paiement doit être strictement positif.")

        paiement = cls(
            id=new_id(),
            addition_id=addition_id,
            service_id=service_id,
            montant=montant,
            forme_paiement=forme_paiement,
            horodatage=horodatage,
        )
        paiement._enregistrer(
            PaiementRecu(
                paiement_id=paiement.id,
                addition_id=addition_id,
                service_id=service_id,
                montant=montant.valeur,
                forme_paiement=forme_paiement.value,
                auteur_id=auteur_id,
            )
        )
        return paiement

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
