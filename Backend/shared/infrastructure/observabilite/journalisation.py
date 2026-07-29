"""Logs structurés : une ligne = un objet JSON.

Render agrège la sortie standard. Du texte libre s'y cherche à l'œil ; du JSON
se filtre. La différence se voit le jour où l'on cherche « toutes les requêtes
de ce compte, ce soir-là ».
"""

from __future__ import annotations

import json
import logging
from typing import Any

# Attributs posés par `logging` lui-même. Tout le reste vient de l'appelant, via
# `extra=`, et part dans la ligne JSON — c'est ce qui rend le format extensible
# sans toucher à ce fichier.
_ATTRIBUTS_STANDARD = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


class FormatteurJSON(logging.Formatter):
    """Sérialise chaque enregistrement en une ligne JSON."""

    def format(self, record: logging.LogRecord) -> str:
        charge: dict[str, Any] = {
            "horodatage": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "niveau": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for cle, valeur in record.__dict__.items():
            if cle not in _ATTRIBUTS_STANDARD and not cle.startswith("_"):
                charge[cle] = valeur
        if record.exc_info:
            charge["exception"] = self.formatException(record.exc_info)

        # `default=str` : un objet non sérialisable ne doit jamais faire échouer
        # l'écriture d'un log — perdre la ligne coûterait plus que l'approximer.
        return json.dumps(charge, ensure_ascii=False, default=str)
