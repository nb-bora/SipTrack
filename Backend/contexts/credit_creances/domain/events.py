"""Événements de domaine du contexte Créances."""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class CreditAccorde(DomainEvent):
    """Né au moment où une addition est payée en crédit."""

    credit_id: str
    client_id: str
    service_id: str
    addition_id: str
    montant: int
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class RemboursementRecu(DomainEvent):
    """Remboursement partiel ou total."""

    remboursement_id: str
    credit_id: str
    client_id: str
    montant: int
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class CreditSolde(DomainEvent):
    """Crédit entièrement remboursé."""

    credit_id: str
    client_id: str
    auteur_id: str
