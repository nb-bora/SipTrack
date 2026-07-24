"""Attribution : le lien indéfectible entre un fait et son répondant.

L'attribution se fait par acte ET par capacité, jamais par rôle figé
(cf. docs/02-modele-metier.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Capacite(StrEnum):
    OPERATRICE = "operatrice"
    SUPERVISEUSE = "superviseuse"


@dataclass(frozen=True)
class Attribution:
    auteur_id: str
    capacite: Capacite
    horodatage: datetime
