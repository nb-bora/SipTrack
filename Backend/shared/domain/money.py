"""Objet-valeur Montant.

Le franc CFA (XAF) n'a pas de sous-unité : les montants sont des entiers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Montant:
    montant: int
    devise: str = "XAF"

    def __post_init__(self) -> None:
        if self.montant < 0:
            raise ValueError("Un montant ne peut pas être négatif.")

    def _verifier_devise(self, autre: Montant) -> None:
        if self.devise != autre.devise:
            raise ValueError(f"Devises incompatibles : {self.devise} vs {autre.devise}.")

    def __add__(self, autre: Montant) -> Montant:
        self._verifier_devise(autre)
        return Montant(self.montant + autre.montant, self.devise)

    def __sub__(self, autre: Montant) -> Montant:
        self._verifier_devise(autre)
        return Montant(self.montant - autre.montant, self.devise)
