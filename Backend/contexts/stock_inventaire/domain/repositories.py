"""Interfaces de persistence (repositories) pour Stock & Inventaire."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .produit import Produit


class ProduitRepository(Protocol):
    """Interface pour charger et sauvegarder les produits."""

    def ajouter(self, produit: Produit) -> None:
        """Crée un produit."""
        ...

    def par_id(self, produit_id: str) -> Produit | None:
        """Charge un produit par son ID."""
        ...

    def du_bar(self, bar_id: str) -> tuple[Produit, ...]:
        """Liste tous les produits d'un bar."""
        ...

    def du_bar_et_nom(self, *, bar_id: str, nom: str) -> Produit | None:
        """Charge un produit par bar et nom unique."""
        ...

    def mettre_a_jour(self, produit: Produit) -> None:
        """Met à jour les quantités d'un produit."""
        ...
