"""Modèles ORM (tables) du contexte Service & Ventes.

Ce sont des **tables**, pas des agrégats : aucune logique métier ici. Le mapping
vers/depuis le domaine est fait par le repository.
"""

from __future__ import annotations

from django.core.serializers.json import DjangoJSONEncoder
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


class MouvementModel(models.Model):
    """Journal d'audit append-only. Ne jamais UPDATE/DELETE (cf. ADR-0003)."""

    id = models.CharField(primary_key=True, max_length=36)
    type = models.CharField(max_length=60)
    auteur_id = models.CharField(max_length=36)
    donnees = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    horodatage_saisie = models.DateTimeField()
    horodatage_reception = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "service_ventes_mouvement"
        ordering = ["horodatage_reception"]

    def __str__(self) -> str:
        return f"{self.type} ({self.id})"
