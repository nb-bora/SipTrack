"""Modèles Django pour Stock & Inventaire."""

from django.db import models


class ProduitModel(models.Model):
    """Modèle persistant d'un produit."""

    id = models.CharField(max_length=36, primary_key=True)
    bar = models.ForeignKey(
        "gouvernance.BarModel",
        on_delete=models.CASCADE,
        related_name="produits",
    )
    nom = models.CharField(max_length=255)
    quantite = models.IntegerField(default=0)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("bar", "nom"),
                name="unique_bar_produit_nom",
            )
        ]
        ordering = ["nom"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.quantite})"
