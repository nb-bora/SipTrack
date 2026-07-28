"""Ports : interfaces de persistance du contexte Gouvernance."""

from __future__ import annotations

from typing import Protocol

from .bar import Bar
from .compte import Compte


class BarRepository(Protocol):
    """Persistence des bars."""

    def ajouter(self, bar: Bar) -> None: ...

    def par_id(self, bar_id: str) -> Bar | None: ...

    def du_proprietaire(self, proprietaire_id: str) -> tuple[Bar, ...]:
        """Tous les bars appartenant à ce proprietaire."""
        ...


class CompteRepository(Protocol):
    """Persistence des comptes utilisateurs."""

    def ajouter(self, compte: Compte) -> None: ...

    def par_id(self, compte_id: str) -> Compte | None: ...

    def du_bar(self, bar_id: str) -> tuple[Compte, ...]:
        """Tous les comptes dans ce bar."""
        ...

    def du_bar_et_user(self, *, bar_id: str, user_id: str) -> Compte | None:
        """Le compte d'un utilisateur dans ce bar, s'il existe."""
        ...

    def mettre_a_jour(self, compte: Compte) -> None: ...
