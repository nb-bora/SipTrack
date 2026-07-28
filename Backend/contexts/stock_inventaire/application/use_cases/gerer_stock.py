"""Cas d'usage : gérer le stock de produits."""

from __future__ import annotations

from contexts.stock_inventaire.application.dto import (
    AjouterStockCommand,
    CorrigerInventaireCommand,
    CreerProduitCommand,
    ProduitDTO,
    VendreCommand,
)
from contexts.stock_inventaire.domain.exceptions import (
    ProduitDejaExistant,
    ProduitIntrouvable,
)
from contexts.stock_inventaire.domain.produit import Produit
from contexts.stock_inventaire.domain.repositories import ProduitRepository
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork


class GererStockHandler:
    """Gérer les produits et les mouvements de stock."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        produits: ProduitRepository,
        journal: Journal,
    ) -> None:
        self._uow = uow
        self._produits = produits
        self._journal = journal

    def creer_produit(self, commande: CreerProduitCommand) -> ProduitDTO:
        """Crée un produit dans le catalogue d'un bar."""
        with self._uow:
            # Vérifier qu'aucun produit de ce bar n'a ce nom.
            existant = self._produits.du_bar_et_nom(bar_id=commande.bar_id, nom=commande.nom)
            if existant is not None:
                raise ProduitDejaExistant(commande.bar_id, commande.nom)

            produit = Produit.creer(
                bar_id=commande.bar_id,
                nom=commande.nom,
                quantite_initiale=commande.quantite_initiale,
            )
            self._produits.ajouter(produit)
            self._journal.enregistrer(produit.evenements_non_publies(), auteur_id="system")
            produit.purger_evenements()
            self._uow.commit()

            return ProduitDTO.depuis_produit(produit)

    def ajouter_stock(self, commande: AjouterStockCommand) -> ProduitDTO:
        """Ajoute du stock à un produit."""
        with self._uow:
            produit = self._produits.par_id(commande.produit_id)
            if produit is None:
                raise ProduitIntrouvable(commande.produit_id)

            produit.ajouter_stock(quantite=commande.quantite, auteur_id=commande.auteur_id)
            self._produits.mettre_a_jour(produit)
            self._journal.enregistrer(
                produit.evenements_non_publies(), auteur_id=commande.auteur_id
            )
            produit.purger_evenements()
            self._uow.commit()

            return ProduitDTO.depuis_produit(produit)

    def vendre(self, commande: VendreCommand) -> ProduitDTO:
        """Enregistre une vente."""
        with self._uow:
            produit = self._produits.par_id(commande.produit_id)
            if produit is None:
                raise ProduitIntrouvable(commande.produit_id)

            produit.vendre(quantite=commande.quantite, auteur_id=commande.auteur_id)
            self._produits.mettre_a_jour(produit)
            self._journal.enregistrer(
                produit.evenements_non_publies(), auteur_id=commande.auteur_id
            )
            produit.purger_evenements()
            self._uow.commit()

            return ProduitDTO.depuis_produit(produit)

    def corriger_inventaire(self, commande: CorrigerInventaireCommand) -> ProduitDTO:
        """Corrige l'inventaire à la quantité déclarée."""
        with self._uow:
            produit = self._produits.par_id(commande.produit_id)
            if produit is None:
                raise ProduitIntrouvable(commande.produit_id)

            produit.corriger_inventaire(
                quantite_nouvelle=commande.quantite_nouvelle,
                raison=commande.raison,
                auteur_id=commande.auteur_id,
            )
            self._produits.mettre_a_jour(produit)
            self._journal.enregistrer(
                produit.evenements_non_publies(), auteur_id=commande.auteur_id
            )
            produit.purger_evenements()
            self._uow.commit()

            return ProduitDTO.depuis_produit(produit)

    def lister_produits(self, bar_id: str) -> tuple[ProduitDTO, ...]:
        """Liste tous les produits d'un bar."""
        produits = self._produits.du_bar(bar_id)
        return tuple(ProduitDTO.depuis_produit(p) for p in produits)
