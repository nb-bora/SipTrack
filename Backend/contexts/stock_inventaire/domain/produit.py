"""Agrégat Produit — un article dans le catalogue d'un bar."""

from __future__ import annotations

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id

from .events import (
    InventaireCorrige,
    ProduitAjoute,
    StockAjoute,
    VenteEnregistree,
)
from .exceptions import QuantiteInsuffisante, QuantiteNegative


class Produit:
    """Un produit avec sa quantité actuelle.

    Jamais de quantité négative — la vente ou l'ajout vérifient les préconditions.
    Chaque mutation s'écrit comme un Fait journalisé.
    """

    def __init__(
        self,
        *,
        id: str,
        bar_id: str,
        nom: str,
        quantite: int,
    ) -> None:
        self.id = id
        self.bar_id = bar_id
        self.nom = nom
        self.quantite = quantite
        self._evenements: list[DomainEvent] = []

    @classmethod
    def creer(cls, *, bar_id: str, nom: str, quantite_initiale: int) -> Produit:
        """Crée un produit dans le catalogue d'un bar."""
        if quantite_initiale < 0:
            raise QuantiteNegative(nom, "création avec quantité négative")

        produit = cls(
            id=new_id(),
            bar_id=bar_id,
            nom=nom,
            quantite=quantite_initiale,
        )
        produit._enregistrer(
            ProduitAjoute(
                produit_id=produit.id,
                bar_id=bar_id,
                nom=nom,
                quantite_initiale=quantite_initiale,
            )
        )
        return produit

    def ajouter_stock(self, *, quantite: int, auteur_id: str) -> None:
        """Ajoute du stock.

        Levée si la quantité à ajouter est négative (utiliser vendre() pour ça).
        """
        if quantite < 0:
            raise QuantiteNegative(self.id, "ajout de quantité négative")

        self.quantite += quantite
        self._enregistrer(
            StockAjoute(
                produit_id=self.id,
                bar_id=self.bar_id,
                quantite_ajoutee=quantite,
                auteur_id=auteur_id,
            )
        )

    def vendre(self, *, quantite: int, auteur_id: str) -> None:
        """Enregistre une vente.

        Levée si la quantité dépasse le stock. Jamais de négatif.
        """
        if quantite < 0:
            raise QuantiteNegative(self.id, "vente de quantité négative")

        if quantite > self.quantite:
            raise QuantiteInsuffisante(self.id, self.quantite, quantite)

        self.quantite -= quantite
        self._enregistrer(
            VenteEnregistree(
                produit_id=self.id,
                bar_id=self.bar_id,
                quantite_vendue=quantite,
                auteur_id=auteur_id,
            )
        )

    def corriger_inventaire(self, *, quantite_nouvelle: int, raison: str, auteur_id: str) -> None:
        """Corrige l'inventaire à la quantité déclarée.

        Utilisé lors d'inventaires physiques. Levée si négatif.
        """
        if quantite_nouvelle < 0:
            raise QuantiteNegative(self.id, f"correction à {quantite_nouvelle}")

        quantite_ancienne = self.quantite
        self.quantite = quantite_nouvelle
        self._enregistrer(
            InventaireCorrige(
                produit_id=self.id,
                bar_id=self.bar_id,
                quantite_ancienne=quantite_ancienne,
                quantite_nouvelle=quantite_nouvelle,
                raison=raison,
                auteur_id=auteur_id,
            )
        )

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
