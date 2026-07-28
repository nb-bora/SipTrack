"""Agrégat racine : Addition.

Une table servie, portant un ensemble de consommations (ventes) non encore réglées.
Aucune dépendance à Django (domaine pur).
"""

from __future__ import annotations

from datetime import datetime

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id

from .enums import StatutAddition
from .events import AdditionOuverte, AdditionReglee
from .exceptions import AdditionDejaCloturee


class Addition:
    def __init__(
        self,
        *,
        id: str,
        service_id: str,
        table_numero: int,
        statut: StatutAddition,
        ouvert_le: datetime,
        ferme_le: datetime | None = None,
    ) -> None:
        self.id = id
        self.service_id = service_id
        self.table_numero = table_numero
        self.statut = statut
        self.ouvert_le = ouvert_le
        self.ferme_le = ferme_le
        self._evenements: list[DomainEvent] = []

    @classmethod
    def ouvrir(
        cls,
        *,
        service_id: str,
        table_numero: int,
        horodatage: datetime,
        auteur_id: str,
    ) -> Addition:
        """Ouvre une nouvelle addition et enregistre le fait correspondant."""
        addition = cls(
            id=new_id(),
            service_id=service_id,
            table_numero=table_numero,
            statut=StatutAddition.OUVERTE,
            ouvert_le=horodatage,
        )
        addition._enregistrer(
            AdditionOuverte(
                addition_id=addition.id,
                service_id=service_id,
                table_numero=table_numero,
                auteur_id=auteur_id,
            )
        )
        return addition

    def accepter_consommation(self) -> None:
        """Vérifie que l'addition peut encore recevoir une consommation.

        Une addition réglée ou abandonnée est close : y rattacher une vente
        reviendrait à modifier une addition déjà présentée au client.
        """
        if self.statut is not StatutAddition.OUVERTE:
            raise AdditionDejaCloturee(self.id)

    def regler(self, *, auteur_id: str, horodatage: datetime) -> None:
        """Régle l'addition (transition Ouverte → Réglée)."""
        if self.statut is not StatutAddition.OUVERTE:
            raise AdditionDejaCloturee(self.id)

        self.statut = StatutAddition.REGLEE
        self.ferme_le = horodatage
        self._enregistrer(
            AdditionReglee(
                addition_id=self.id,
                service_id=self.service_id,
                table_numero=self.table_numero,
                auteur_id=auteur_id,
            )
        )

    # --- Gestion des événements ------------------------------------------
    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
