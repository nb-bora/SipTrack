"""Adaptateurs Django du contexte Catalogue."""

from __future__ import annotations

from contexts.catalogue.application.dto import ProduitDTO
from contexts.catalogue.domain.produit import Produit
from contexts.catalogue.infrastructure.django_app.models import ProduitModel
from shared.domain.money import Montant


def _vers_produit(modele: ProduitModel) -> Produit:
    return Produit(
        id=modele.id,
        bar_id=modele.bar_id,
        nom=modele.nom,
        prix=Montant(modele.prix),
        en_vente=modele.en_vente,
    )


class DjangoProduitRepository:
    def ajouter(self, produit: Produit) -> None:
        ProduitModel.objects.create(
            id=produit.id,
            bar_id=produit.bar_id,
            nom=produit.nom,
            prix=produit.prix.valeur,
            en_vente=produit.en_vente,
        )

    def par_id(self, produit_id: str) -> Produit | None:
        modele = ProduitModel.objects.filter(id=produit_id).first()
        return _vers_produit(modele) if modele is not None else None

    def par_bar_et_nom(self, *, bar_id: str, nom: str) -> Produit | None:
        modele = ProduitModel.objects.filter(bar_id=bar_id, nom=nom).first()
        return _vers_produit(modele) if modele is not None else None

    def du_bar(self, bar_id: str) -> tuple[Produit, ...]:
        return tuple(_vers_produit(m) for m in ProduitModel.objects.filter(bar_id=bar_id))

    def mettre_a_jour(self, produit: Produit) -> None:
        ProduitModel.objects.filter(id=produit.id).update(
            prix=produit.prix.valeur,
            en_vente=produit.en_vente,
        )


class DjangoCatalogueQueryService:
    def du_bar(self, bar_id: str) -> tuple[ProduitDTO, ...]:
        return tuple(
            ProduitDTO(
                id=m.id,
                bar_id=m.bar_id,
                nom=m.nom,
                prix=m.prix,
                en_vente=m.en_vente,
            )
            for m in ProduitModel.objects.filter(bar_id=bar_id)
        )
