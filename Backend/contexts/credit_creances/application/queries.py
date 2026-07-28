"""Ports de lecture (CQRS) du contexte Crédit & Créances.

Les soldes ne sont jamais stockés : ils se recalculent à la lecture depuis les
crédits et leurs remboursements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CreanceDTO:
    """Une dette et son état, vue de la gérante."""

    credit_id: str
    client_id: str
    client_nom: str
    service_id: str
    addition_id: str
    montant: int
    rembourse: int
    reste: int
    statut: str


@dataclass(frozen=True)
class EncoursClientDTO:
    """Ce qu'un client doit au bar, tous crédits confondus."""

    client_id: str
    client_nom: str
    total_du: int
    total_rembourse: int
    reste: int
    creances: tuple[CreanceDTO, ...]


class EncoursQueryService(Protocol):
    """Port de lecture des encours."""

    def par_client(self, client_id: str) -> EncoursClientDTO | None:
        """L'encours d'un client, avec le détail de ses créances."""
        ...

    def tous(self, bar_id: str) -> tuple[EncoursClientDTO, ...]:
        """Tous les clients d'un bar ayant une dette non éteinte."""
        ...
