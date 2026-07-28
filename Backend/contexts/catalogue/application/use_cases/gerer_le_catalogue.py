"""Cas d'usage du catalogue : inscrire, tarifer, retirer.

Trois gestes de gestion réunis : ils partagent le même agrégat, les mêmes
dépendances, et se lisent mieux côte à côte que dispersés dans trois fichiers
de vingt lignes.
"""

from __future__ import annotations

from contexts.catalogue.application.dto import (
    ChangerLeTarifCommand,
    InscrireProduitCommand,
    ProduitDTO,
    RetirerProduitCommand,
)
from contexts.catalogue.domain.exceptions import ProduitDejaInscrit, ProduitIntrouvable
from contexts.catalogue.domain.produit import Produit
from contexts.catalogue.domain.repositories import ProduitRepository
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork
from shared.domain.money import Montant


class GererLeCatalogueHandler:
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

    def inscrire(self, commande: InscrireProduitCommand) -> ProduitDTO:
        with self._uow:
            # Deux lignes pour la même bière rendraient tout comptage ambigu.
            if self._produits.par_bar_et_nom(bar_id=commande.bar_id, nom=commande.nom):
                raise ProduitDejaInscrit(commande.bar_id, commande.nom)

            produit = Produit.inscrire(
                bar_id=commande.bar_id,
                nom=commande.nom,
                prix=Montant(commande.prix),
                auteur_id=commande.auteur_id,
            )
            self._produits.ajouter(produit)
            return self._publier(produit, commande.auteur_id)

    def changer_le_tarif(self, commande: ChangerLeTarifCommand) -> ProduitDTO:
        with self._uow:
            produit = self._charger(commande.produit_id)
            produit.changer_le_tarif(
                nouveau_prix=Montant(commande.nouveau_prix),
                auteur_id=commande.auteur_id,
            )
            self._produits.mettre_a_jour(produit)
            return self._publier(produit, commande.auteur_id)

    def retirer(self, commande: RetirerProduitCommand) -> ProduitDTO:
        with self._uow:
            produit = self._charger(commande.produit_id)
            produit.retirer_de_la_vente(auteur_id=commande.auteur_id)
            self._produits.mettre_a_jour(produit)
            return self._publier(produit, commande.auteur_id)

    def _charger(self, produit_id: str) -> Produit:
        produit = self._produits.par_id(produit_id)
        if produit is None:
            raise ProduitIntrouvable(produit_id)
        return produit

    def _publier(self, produit: Produit, auteur_id: str) -> ProduitDTO:
        self._journal.enregistrer(produit.evenements_non_publies(), auteur_id=auteur_id)
        produit.purger_evenements()
        self._uow.commit()
        return ProduitDTO.depuis(produit)
