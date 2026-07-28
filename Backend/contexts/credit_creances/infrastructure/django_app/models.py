"""Modèles Django du contexte Crédit & Créances."""

from django.db import models


class ClientModel(models.Model):
    """Persistance de l'agrégat Client."""

    id = models.CharField(max_length=36, primary_key=True)
    bar_id = models.CharField(max_length=36)
    nom = models.CharField(max_length=120)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credit_creances_client"
        ordering = ["nom"]
        constraints = [
            models.UniqueConstraint(
                fields=("bar_id", "nom"),
                name="un_client_par_nom_et_bar",
            ),
        ]

    def __str__(self) -> str:
        return self.nom


class CreditModel(models.Model):
    """Persistance de l'agrégat Crédit.

    Ce qui a été remboursé n'est pas stocké ici : il se recalcule depuis les
    remboursements. Seul le statut est conservé, comme pour une addition.
    """

    id = models.CharField(max_length=36, primary_key=True)
    client = models.ForeignKey(
        ClientModel,
        on_delete=models.PROTECT,
        related_name="credits",
    )
    service_id = models.CharField(max_length=36)
    # Une addition n'engendre qu'une créance : la contrainte tient même si deux
    # requêtes concurrentes passent la vérification applicative.
    addition_id = models.CharField(max_length=36, unique=True)
    montant = models.PositiveIntegerField()
    statut = models.CharField(max_length=16)
    ne_le = models.DateTimeField()

    class Meta:
        db_table = "credit_creances_credit"
        ordering = ["ne_le"]
        indexes = [models.Index(fields=("client", "statut"))]

    def __str__(self) -> str:
        return f"{self.montant} XAF — {self.statut}"


class RemboursementModel(models.Model):
    """Persistance de l'agrégat Remboursement.

    Chaque remboursement est une ligne, jamais un total mis à jour : c'est ce
    qui permet de dire qui a encaissé quoi, et quand.
    """

    id = models.CharField(max_length=36, primary_key=True)
    credit = models.ForeignKey(
        CreditModel,
        on_delete=models.PROTECT,
        related_name="remboursements",
    )
    client_id = models.CharField(max_length=36)
    montant = models.PositiveIntegerField()
    auteur_id = models.CharField(max_length=36)
    horodatage = models.DateTimeField()

    class Meta:
        db_table = "credit_creances_remboursement"
        ordering = ["horodatage"]

    def __str__(self) -> str:
        return f"{self.montant} XAF"
