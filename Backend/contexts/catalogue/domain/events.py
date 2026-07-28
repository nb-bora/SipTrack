"""Événements de domaine du contexte Catalogue."""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ProduitInscrit(DomainEvent):
    produit_id: str
    bar_id: str
    nom: str
    prix: int
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class TarifModifie(DomainEvent):
    """Un changement de prix, avec l'ancien et le nouveau.

    Journalisé parce qu'une recette qui bouge doit pouvoir s'expliquer : sans ce
    Fait, une baisse de chiffre d'affaires serait indiscernable d'un vol.
    """

    produit_id: str
    bar_id: str
    ancien_prix: int
    nouveau_prix: int
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class ProduitRetire(DomainEvent):
    """Retiré de la vente, jamais supprimé : les ventes passées le référencent."""

    produit_id: str
    bar_id: str
    auteur_id: str
