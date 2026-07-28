"""Modèles ORM (tables) du contexte Service & Ventes.

Ce sont des **tables**, pas des agrégats : aucune logique métier ici. Le mapping
vers/depuis le domaine est fait par le repository.
"""

from __future__ import annotations

from django.db import models


class ServiceModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    bar_id = models.CharField(max_length=36)
    responsable_id = models.CharField(max_length=36)
    responsable_capacite = models.CharField(max_length=20)
    fond_de_caisse = models.PositiveIntegerField()
    statut = models.CharField(max_length=20)
    ouvert_le = models.DateTimeField()
    clos_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "service_ventes_service"

    def __str__(self) -> str:
        return f"Service {self.id} ({self.statut})"


class VenteModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    service = models.ForeignKey(ServiceModel, on_delete=models.PROTECT, related_name="ventes")
    # Nullable : une vente au comptoir n'est rattachée à aucune table.
    addition = models.ForeignKey(
        "AdditionModel",
        on_delete=models.PROTECT,
        related_name="lignes",
        null=True,
        blank=True,
    )
    produit_id = models.CharField(max_length=36)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.PositiveIntegerField()
    montant_total = models.PositiveIntegerField()
    forme_paiement = models.CharField(max_length=20)
    horodatage = models.DateTimeField()

    class Meta:
        db_table = "service_ventes_vente"
        ordering = ["horodatage"]

    def __str__(self) -> str:
        return f"Vente {self.id} ({self.montant_total} XAF)"


class VersementModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    service = models.ForeignKey(ServiceModel, on_delete=models.PROTECT, related_name="versements")
    serveuse_id = models.CharField(max_length=36)
    attendu = models.PositiveIntegerField()
    verse = models.PositiveIntegerField()
    ecart = models.IntegerField()
    horodatage = models.DateTimeField()

    class Meta:
        db_table = "service_ventes_versement"
        ordering = ["horodatage"]
        # Une serveuse ne verse qu'une fois par service.
        constraints = [
            models.UniqueConstraint(
                fields=["service", "serveuse_id"],
                name="un_versement_par_serveuse_et_service",
            )
        ]

    def __str__(self) -> str:
        return f"Versement {self.serveuse_id} ({self.verse} XAF, ecart {self.ecart})"


class PaiementModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    addition = models.ForeignKey(
        "AdditionModel", on_delete=models.PROTECT, related_name="paiements"
    )
    service = models.ForeignKey(ServiceModel, on_delete=models.PROTECT, related_name="paiements")
    auteur_id = models.CharField(max_length=36)
    montant = models.PositiveIntegerField()
    forme_paiement = models.CharField(max_length=20)
    horodatage = models.DateTimeField()

    class Meta:
        db_table = "service_ventes_paiement"
        ordering = ["horodatage"]

    def __str__(self) -> str:
        return f"Paiement {self.montant} XAF ({self.forme_paiement})"


class AdditionModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    service = models.ForeignKey(ServiceModel, on_delete=models.PROTECT, related_name="additions")
    table_numero = models.PositiveIntegerField()
    statut = models.CharField(max_length=20)
    ouvert_le = models.DateTimeField()
    ferme_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "service_ventes_addition"
        ordering = ["ouvert_le"]

    def __str__(self) -> str:
        return f"Addition table {self.table_numero} ({self.statut})"
