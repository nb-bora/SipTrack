"""Énumérations du contexte Créances."""

from enum import Enum


class StatutCredit(Enum):
    """Cycle de vie du crédit : du moment où il naît au remboursement total."""

    NE = "ne"
    SOLDE = "solde"

    def __str__(self) -> str:
        return self.value
