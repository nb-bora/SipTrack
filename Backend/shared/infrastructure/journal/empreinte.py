"""Empreinte d'un Mouvement, et chaînage au précédent.

Chaque Mouvement porte l'empreinte du précédent : altérer une ligne ancienne
casse toutes les empreintes qui suivent. On ne peut donc pas réécrire l'histoire
discrètement — il faudrait recalculer la chaîne entière, ce qu'une vérification
détecte en la recomparant à ce qui a été signé au fil de l'eau.

La fonction est **pure** : même entrée, même empreinte, aujourd'hui comme dans
trois ans. C'est la condition pour qu'une vérification ait un sens.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder

# Empreinte conventionnelle du « rien » qui précède le premier Mouvement.
GENESE = "0" * 64


def calculer_empreinte(
    *,
    identifiant: str,
    type_evenement: str,
    auteur_id: str,
    donnees: dict[str, Any],
    horodatage_saisie: datetime,
    sequence: int,
    empreinte_precedente: str,
) -> str:
    """SHA-256 du contenu du Mouvement, chaîné au précédent.

    `donnees` est encodé avec l'encodeur qui sert aussi au stockage : sans cela
    une date vaudrait `datetime(...)` à l'écriture et `"2026-..."` à la
    relecture, et l'empreinte ne serait pas reproductible.
    """
    charge = json.dumps(
        {
            "id": identifiant,
            "type": type_evenement,
            "auteur_id": auteur_id,
            "donnees": donnees,
            "horodatage_saisie": horodatage_saisie,
            "sequence": sequence,
            "empreinte_precedente": empreinte_precedente,
        },
        cls=DjangoJSONEncoder,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(charge.encode("utf-8")).hexdigest()
