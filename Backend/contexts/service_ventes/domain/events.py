"""Événements de domaine du contexte Service & Ventes."""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ServiceOuvert(DomainEvent):
    service_id: str
    bar_id: str
    auteur_id: str
    fond_de_caisse: int
