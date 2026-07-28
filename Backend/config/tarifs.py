"""Adaptateur : brancher le port « prix d'un produit » sur le Catalogue.

Service & Ventes demande un prix qui fait autorité ; le Catalogue le détient.
Ni l'un ni l'autre ne se connaît : ce module, qui appartient à la composition
root, est le seul autorisé à voir les deux (ADR-0005).

Même motif que `config/creances.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contexts.catalogue.domain.exceptions import (
    ProduitIntrouvable,
    ProduitRetireDeLaVente,
)
from contexts.service_ventes.application.ports import ArticleVendable
from contexts.service_ventes.domain.exceptions import ProduitNonVendable

if TYPE_CHECKING:
    from contexts.catalogue.domain.repositories import ProduitRepository


class TarifViaCatalogue:
    """Implémente `TarifDuProduit` en lisant le catalogue."""

    def __init__(self, produits: ProduitRepository) -> None:
        self._produits = produits

    def prix_de(self, *, produit_id: str, bar_id: str) -> ArticleVendable:
        produit = self._produits.par_id(produit_id)

        # Un produit d'un autre bar est, d'ici, inexistant : le catalogue de
        # l'un ne fixe pas les prix de l'autre.
        if produit is None or produit.bar_id != bar_id:
            raise ProduitNonVendable(produit_id, "inconnu du catalogue de ce bar")

        try:
            prix = produit.prix_de_vente()
        except (ProduitRetireDeLaVente, ProduitIntrouvable) as erreur:
            # Traduite dans le vocabulaire de l'appelant : Service & Ventes n'a
            # pas à connaître les exceptions d'un contexte qu'il ignore.
            raise ProduitNonVendable(produit_id, "retiré de la vente") from erreur

        return ArticleVendable(produit_id=produit.id, prix_unitaire=prix.valeur)
