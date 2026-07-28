"""Table du journal d'audit.

C'est une **table**, pas un agrégat : aucune logique métier ici.
"""

from __future__ import annotations

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class JournalInalterable(Exception):
    """Tentative de modifier ou supprimer un Fait déjà journalisé."""


class MouvementModel(models.Model):
    """Journal d'audit append-only (cf. ADR-0003).

    L'append-only n'est pas une simple convention : un déclencheur PostgreSQL
    refuse tout `UPDATE`, `DELETE` et `TRUNCATE` sur cette table, et chaque
    ligne porte l'empreinte de la précédente. Altérer un Mouvement ancien casse
    toutes les empreintes suivantes — c'est ce qui rend le registre opposable.
    """

    id = models.CharField(primary_key=True, max_length=36)
    # Ordre d'écriture strict : c'est lui qui définit « le Mouvement précédent ».
    sequence = models.BigIntegerField(unique=True)
    type = models.CharField(max_length=60)
    auteur_id = models.CharField(max_length=36)
    donnees = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    horodatage_saisie = models.DateTimeField()
    horodatage_reception = models.DateTimeField(auto_now_add=True)
    empreinte = models.CharField(max_length=64, unique=True)
    empreinte_precedente = models.CharField(max_length=64)

    class Meta:
        db_table = "journal_mouvement"
        ordering = ["sequence"]

    def __str__(self) -> str:
        return f"{self.type} ({self.id})"

    def save(self, *args: object, **kwargs: object) -> None:
        """Interdit la réécriture côté Python, en plus du refus en base.

        Le déclencheur PostgreSQL est la vraie garantie — il protège aussi d'un
        accès direct à la base, qui est justement le scénario contre lequel un
        journal d'audit existe. Cette garde-ci ne fait qu'échouer plus tôt, avec
        un message compréhensible.
        """
        if not self._state.adding:
            raise JournalInalterable(
                "Un Mouvement déjà journalisé ne se modifie pas : "
                "une correction s'écrit par contre-passation."
            )
        super().save(*args, **kwargs)  # type: ignore[arg-type]

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        raise JournalInalterable("Un Mouvement ne se supprime pas.")
