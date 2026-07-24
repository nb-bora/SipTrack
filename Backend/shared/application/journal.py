"""Port : Journal.

Le journal d'audit append-only. Il enregistre les événements de domaine comme
faits inaltérables (cf. ADR-0003). L'implémentation concrète vit en infrastructure.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from shared.domain.events import DomainEvent


class Journal(Protocol):
    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None: ...
