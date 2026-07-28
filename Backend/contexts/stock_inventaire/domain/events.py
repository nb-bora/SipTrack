"""Événements du contexte Stock & Inventaire.

Chaque mouvement de stock est un Fait journalisé : ajout, vente, correction.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ProduitAjoute(DomainEvent):
    """Un produit rejoint le catalogue d'un bar."""

    produit_id: str
    bar_id: str
    nom: str
    quantite_initiale: int


@dataclass(frozen=True, kw_only=True)
class StockAjoute(DomainEvent):
    """Du stock est ajouté pour un produit."""

    produit_id: str
    bar_id: str
    quantite_ajoutee: int
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class VenteEnregistree(DomainEvent):
    """Une quantité de produit est enregistrée comme vendue."""

    produit_id: str
    bar_id: str
    quantite_vendue: int
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class InventaireCorrige(DomainEvent):
    """L'inventaire est corrigé à la quantité déclarée."""

    produit_id: str
    bar_id: str
    quantite_ancienne: int
    quantite_nouvelle: int
    raison: str
    auteur_id: str
