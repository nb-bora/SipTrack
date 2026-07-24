"""Objets de transfert (commandes et vues) de la couche application.

Aucun modèle ORM ni agrégat n'est exposé hors des couches internes : on passe
par ces DTO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contexts.service_ventes.domain.service import Service


@dataclass(frozen=True)
class OuvrirServiceCommand:
    bar_id: str
    auteur_id: str
    capacite: str
    fond_de_caisse: int


@dataclass(frozen=True)
class ServiceDTO:
    id: str
    bar_id: str
    statut: str
    fond_de_caisse: int
    ouvert_le: str

    @classmethod
    def depuis(cls, service: Service) -> ServiceDTO:
        return cls(
            id=service.id,
            bar_id=service.bar_id,
            statut=service.statut.value,
            fond_de_caisse=service.fond_de_caisse.montant,
            ouvert_le=service.ouvert_le.isoformat(),
        )
