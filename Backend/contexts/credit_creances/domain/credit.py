"""Agrégat racine : Crédit.

Une dette née quand une consommation part sans argent en face. Petit agrégat
(cf. ADR-0004) qui référence son client, son service et son addition par
identifiant.

Le crédit ne porte **pas** ce qui a été remboursé : cette somme se recalcule à
la lecture depuis les remboursements, comme le total d'une addition se recalcule
depuis ses ventes. Un solde stocké est un solde qui finit par mentir.
"""

from __future__ import annotations

from datetime import datetime

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.domain.money import Montant

from .enums import StatutCredit
from .events import CreditAccorde, CreditSolde


class Credit:
    def __init__(
        self,
        *,
        id: str,
        client_id: str,
        service_id: str,
        addition_id: str,
        montant: Montant,
        statut: StatutCredit,
        ne_le: datetime,
    ) -> None:
        self.id = id
        self.client_id = client_id
        self.service_id = service_id
        self.addition_id = addition_id
        self.montant = montant
        self.statut = statut
        self.ne_le = ne_le
        self._evenements: list[DomainEvent] = []

    @classmethod
    def accorder(
        cls,
        *,
        client_id: str,
        service_id: str,
        addition_id: str,
        montant: Montant,
        horodatage: datetime,
        auteur_id: str,
    ) -> Credit:
        """Ouvre la dette au nom d'un client."""
        credit = cls(
            id=new_id(),
            client_id=client_id,
            service_id=service_id,
            addition_id=addition_id,
            montant=montant,
            statut=StatutCredit.NE,
            ne_le=horodatage,
        )
        credit._enregistrer(
            CreditAccorde(
                credit_id=credit.id,
                client_id=client_id,
                service_id=service_id,
                addition_id=addition_id,
                montant=montant.valeur,
                auteur_id=auteur_id,
            )
        )
        return credit

    def solder(self, *, auteur_id: str) -> None:
        """Éteint la dette.

        Conséquence du dernier franc reçu, jamais une déclaration : seul le cas
        d'usage, qui sait ce qui a été remboursé, décide de l'appeler.
        """
        self.statut = StatutCredit.SOLDE
        self._enregistrer(
            CreditSolde(
                credit_id=self.id,
                client_id=self.client_id,
                auteur_id=auteur_id,
            )
        )

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
