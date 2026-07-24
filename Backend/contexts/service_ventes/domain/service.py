"""Agrégat racine : Service.

Une période de responsabilité, de l'ouverture à la clôture. Porte ses invariants
et produit des événements de domaine. Aucune dépendance à Django (domaine pur).
"""

from __future__ import annotations

from datetime import datetime

from shared.domain.attribution import Attribution
from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.domain.money import Montant

from .enums import StatutService
from .events import ServiceOuvert


class Service:
    def __init__(
        self,
        *,
        id: str,
        bar_id: str,
        responsable: Attribution,
        fond_de_caisse: Montant,
        statut: StatutService,
        ouvert_le: datetime,
        clos_le: datetime | None = None,
    ) -> None:
        self.id = id
        self.bar_id = bar_id
        self.responsable = responsable
        self.fond_de_caisse = fond_de_caisse
        self.statut = statut
        self.ouvert_le = ouvert_le
        self.clos_le = clos_le
        self._evenements: list[DomainEvent] = []

    @classmethod
    def ouvrir(
        cls,
        *,
        bar_id: str,
        responsable: Attribution,
        fond_de_caisse: Montant,
        horodatage: datetime,
    ) -> Service:
        """Ouvre un nouveau service et enregistre le fait correspondant."""
        service = cls(
            id=new_id(),
            bar_id=bar_id,
            responsable=responsable,
            fond_de_caisse=fond_de_caisse,
            statut=StatutService.OUVERT,
            ouvert_le=horodatage,
        )
        service._enregistrer(
            ServiceOuvert(
                service_id=service.id,
                bar_id=bar_id,
                auteur_id=responsable.auteur_id,
                fond_de_caisse=fond_de_caisse.montant,
            )
        )
        return service

    # --- Gestion des événements ------------------------------------------
    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
