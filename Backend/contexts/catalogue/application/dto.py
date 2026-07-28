"""Objets de transfert de données du contexte Catalogue."""

from __future__ import annotations

from dataclasses import dataclass

from contexts.catalogue.domain.produit import Produit


@dataclass(frozen=True)
class InscrireProduitCommand:
    bar_id: str
    nom: str
    prix: int
    auteur_id: str


@dataclass(frozen=True)
class ChangerLeTarifCommand:
    produit_id: str
    nouveau_prix: int
    auteur_id: str


@dataclass(frozen=True)
class RetirerProduitCommand:
    produit_id: str
    auteur_id: str


@dataclass(frozen=True)
class ProduitDTO:
    id: str
    bar_id: str
    nom: str
    prix: int
    en_vente: bool

    @classmethod
    def depuis(cls, produit: Produit) -> ProduitDTO:
        return cls(
            id=produit.id,
            bar_id=produit.bar_id,
            nom=produit.nom,
            prix=produit.prix.valeur,
            en_vente=produit.en_vente,
        )
