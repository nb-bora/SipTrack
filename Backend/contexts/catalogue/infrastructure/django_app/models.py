"""Modèles Django du contexte Catalogue."""

from django.db import models


class ProduitModel(models.Model):
    """Persistance de l'agrégat Produit.

    `prix` est le tarif **en vigueur**. Le prix d'une vente passée vit sur la
    ligne de vente, pas ici : changer un tarif ce soir ne doit pas réécrire la
    valeur des nuits précédentes.
    """

    id = models.CharField(max_length=36, primary_key=True)
    bar_id = models.CharField(max_length=36)
    nom = models.CharField(max_length=120)
    prix = models.PositiveIntegerField()
    # Retiré, jamais supprimé : les ventes passées le référencent.
    en_vente = models.BooleanField(default=True)

    class Meta:
        db_table = "catalogue_produit"
        ordering = ["nom"]
        constraints = [
            models.UniqueConstraint(
                fields=("bar_id", "nom"),
                name="un_produit_par_nom_et_bar",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nom} — {self.prix} XAF"
