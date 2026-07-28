"""Repositories pour Stock & Inventaire."""

from __future__ import annotations

from django.db import IntegrityError

from contexts.stock_inventaire.domain.exceptions import ProduitDejaExistant
from contexts.stock_inventaire.domain.produit import Produit
from contexts.stock_inventaire.infrastructure.django_app.models import ProduitModel


def _vers_produit(modele: ProduitModel) -> Produit:
    """Reconstitue un agrégat Produit depuis le modèle Django."""
    return Produit(
        id=modele.id,
        bar_id=modele.bar_id,
        nom=modele.nom,
        quantite=modele.quantite,
    )


class DjangoProduitRepository:
    """Persistence des produits."""

    def ajouter(self, produit: Produit) -> None:
        try:
            ProduitModel.objects.create(
                id=produit.id,
                bar_id=produit.bar_id,
                nom=produit.nom,
                quantite=produit.quantite,
            )
        except IntegrityError as e:
            if "unique constraint" in str(e).lower():
                raise ProduitDejaExistant(produit.bar_id, produit.nom) from e
            raise

    def par_id(self, produit_id: str) -> Produit | None:
        modele = ProduitModel.objects.filter(id=produit_id).first()
        return _vers_produit(modele) if modele is not None else None

    def du_bar(self, bar_id: str) -> tuple[Produit, ...]:
        modeles = ProduitModel.objects.filter(bar_id=bar_id)
        return tuple(_vers_produit(m) for m in modeles)

    def du_bar_et_nom(self, *, bar_id: str, nom: str) -> Produit | None:
        modele = ProduitModel.objects.filter(bar_id=bar_id, nom=nom).first()
        return _vers_produit(modele) if modele is not None else None

    def mettre_a_jour(self, produit: Produit) -> None:
        ProduitModel.objects.filter(id=produit.id).update(
            quantite=produit.quantite,
        )
