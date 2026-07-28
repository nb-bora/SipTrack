"""Ports : interfaces de persistance du contexte Catalogue."""

from __future__ import annotations

from typing import Protocol

from .produit import Produit


class ProduitRepository(Protocol):
    def ajouter(self, produit: Produit) -> None: ...

    def par_id(self, produit_id: str) -> Produit | None: ...

    def par_bar_et_nom(self, *, bar_id: str, nom: str) -> Produit | None: ...

    def du_bar(self, bar_id: str) -> tuple[Produit, ...]:
        """Tout le catalogue d'un bar, retirés compris."""
        ...

    def mettre_a_jour(self, produit: Produit) -> None: ...
