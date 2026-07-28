"""Ports : interfaces de persistance du contexte Crédit & Créances."""

from __future__ import annotations

from typing import Protocol

from .client import Client
from .credit import Credit
from .remboursement import Remboursement


class ClientRepository(Protocol):
    """Port de persistance pour les Clients."""

    def ajouter(self, client: Client) -> None: ...

    def par_id(self, client_id: str) -> Client | None: ...

    def par_bar_et_nom(self, *, bar_id: str, nom: str) -> Client | None: ...


class CreditRepository(Protocol):
    """Port de persistance pour les Crédits."""

    def ajouter(self, credit: Credit) -> None: ...

    def par_id(self, credit_id: str) -> Credit | None: ...

    def par_addition(self, addition_id: str) -> Credit | None: ...

    def mettre_a_jour(self, credit: Credit) -> None: ...


class RemboursementRepository(Protocol):
    """Port de persistance pour les Remboursements."""

    def ajouter(self, remboursement: Remboursement) -> None: ...

    def total_rembourse(self, credit_id: str) -> int:
        """Somme des remboursements reçus sur ce crédit."""
        ...
