"""Agrégat racine : Produit.

Ce que le bar vend, et à quel prix **aujourd'hui**. Le prix porté ici est le
tarif en vigueur, pas celui d'une vente passée : une vente copie le prix au
moment où elle est saisie, et le garde. Sans cette copie, changer un tarif ce
soir réécrirait la valeur de toutes les nuits précédentes.
"""

from __future__ import annotations

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.domain.money import Montant

from .events import ProduitInscrit, ProduitRetire, TarifModifie
from .exceptions import ProduitRetireDeLaVente, TarifInchange


class Produit:
    def __init__(
        self,
        *,
        id: str,
        bar_id: str,
        nom: str,
        prix: Montant,
        en_vente: bool = True,
    ) -> None:
        self.id = id
        self.bar_id = bar_id
        self.nom = nom
        self.prix = prix
        self.en_vente = en_vente
        self._evenements: list[DomainEvent] = []

    @classmethod
    def inscrire(
        cls,
        *,
        bar_id: str,
        nom: str,
        prix: Montant,
        auteur_id: str,
    ) -> Produit:
        produit = cls(id=new_id(), bar_id=bar_id, nom=nom, prix=prix)
        produit._enregistrer(
            ProduitInscrit(
                produit_id=produit.id,
                bar_id=bar_id,
                nom=nom,
                prix=prix.valeur,
                auteur_id=auteur_id,
            )
        )
        return produit

    def changer_le_tarif(self, *, nouveau_prix: Montant, auteur_id: str) -> None:
        """Change le prix en vigueur, et laisse une trace de l'ancien.

        Retenir l'ancien prix dans le Fait est ce qui permet d'expliquer une
        recette qui bouge : sans lui, une baisse de chiffre d'affaires serait
        indiscernable d'un vol.
        """
        if nouveau_prix.valeur == self.prix.valeur:
            raise TarifInchange(self.id, self.prix.valeur)

        ancien = self.prix
        self.prix = nouveau_prix
        self._enregistrer(
            TarifModifie(
                produit_id=self.id,
                bar_id=self.bar_id,
                ancien_prix=ancien.valeur,
                nouveau_prix=nouveau_prix.valeur,
                auteur_id=auteur_id,
            )
        )

    def retirer_de_la_vente(self, *, auteur_id: str) -> None:
        """Retire le produit de la vente sans jamais l'effacer.

        Les ventes passées le référencent : le supprimer rendrait illisible
        l'historique qu'on cherche précisément à protéger.
        """
        self.en_vente = False
        self._enregistrer(
            ProduitRetire(produit_id=self.id, bar_id=self.bar_id, auteur_id=auteur_id)
        )

    def prix_de_vente(self) -> Montant:
        """Le prix à appliquer à une vente saisie maintenant."""
        if not self.en_vente:
            raise ProduitRetireDeLaVente(self.id)
        return self.prix

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
