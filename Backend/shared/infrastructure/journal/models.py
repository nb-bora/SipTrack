"""Table du journal d'audit.

C'est une **table**, pas un agrégat : aucune logique métier ici.
"""

from __future__ import annotations

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class MouvementModel(models.Model):
    """Journal d'audit append-only. Ne jamais UPDATE/DELETE (cf. ADR-0003).

    L'append-only n'est aujourd'hui qu'une convention : rien en base ne
    l'impose. C'est l'objet du durcissement à venir (chaînage d'empreintes et
    refus d'UPDATE/DELETE côté PostgreSQL).
    """

    id = models.CharField(primary_key=True, max_length=36)
    type = models.CharField(max_length=60)
    auteur_id = models.CharField(max_length=36)
    donnees = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    horodatage_saisie = models.DateTimeField()
    horodatage_reception = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "journal_mouvement"
        ordering = ["horodatage_reception"]

    def __str__(self) -> str:
        return f"{self.type} ({self.id})"
