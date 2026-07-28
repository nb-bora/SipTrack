"""Ports de lecture du contexte Catalogue."""

from __future__ import annotations

from typing import Protocol

from contexts.catalogue.application.dto import ProduitDTO


class CatalogueQueryService(Protocol):
    def du_bar(self, bar_id: str) -> tuple[ProduitDTO, ...]:
        """Le catalogue d'un bar. Les produits retirés y figurent, marqués."""
        ...
