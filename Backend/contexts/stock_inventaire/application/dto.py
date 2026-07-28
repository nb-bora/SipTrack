"""DTOs du contexte Stock & Inventaire."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contexts.stock_inventaire.domain.produit import Produit


@dataclass(frozen=True)
class CreerProduitCommand:
    """Créer un produit dans le catalogue."""

    bar_id: str
    nom: str
    quantite_initiale: int


@dataclass(frozen=True)
class AjouterStockCommand:
    """Ajouter du stock à un produit."""

    produit_id: str
    quantite: int
    auteur_id: str


@dataclass(frozen=True)
class VendreCommand:
    """Enregistrer une vente."""

    produit_id: str
    quantite: int
    auteur_id: str


@dataclass(frozen=True)
class CorrigerInventaireCommand:
    """Corriger l'inventaire."""

    produit_id: str
    quantite_nouvelle: int
    raison: str
    auteur_id: str


@dataclass(frozen=True)
class ProduitDTO:
    """Représentation d'un produit."""

    id: str
    bar_id: str
    nom: str
    quantite: int

    @classmethod
    def depuis_produit(cls, produit: Produit) -> ProduitDTO:
        return cls(
            id=produit.id,
            bar_id=produit.bar_id,
            nom=produit.nom,
            quantite=produit.quantite,
        )
