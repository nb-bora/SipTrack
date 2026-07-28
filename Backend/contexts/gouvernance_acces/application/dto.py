"""DTOs du contexte Gouvernance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contexts.gouvernance_acces.domain.bar import Bar
    from contexts.gouvernance_acces.domain.compte import Compte


@dataclass(frozen=True)
class CreerBarCommand:
    """Créer un bar appartenant au propriétaire authentifié."""

    nom: str
    proprietaire_id: str  # Tiré du jeton, jamais du corps de la requête


@dataclass(frozen=True)
class CreerCompteCommand:
    """Créer un compte utilisateur dans un bar."""

    bar_id: str
    user_id: str  # L'utilisateur Django à rattacher
    capacites_initiales: frozenset[str]
    auteur_id: str  # Celui qui crée le compte


@dataclass(frozen=True)
class AccorderCapaciteCommand:
    """Accorder une capacité à un compte."""

    compte_id: str
    capacite: str
    auteur_id: str


@dataclass(frozen=True)
class RetirerCapaciteCommand:
    """Retirer une capacité."""

    compte_id: str
    capacite: str
    auteur_id: str


@dataclass(frozen=True)
class BarDTO:
    """Représentation d'un bar."""

    id: str
    nom: str
    proprietaire_id: str

    @classmethod
    def depuis_bar(cls, bar: Bar) -> BarDTO:
        return cls(id=bar.id, nom=bar.nom, proprietaire_id=bar.proprietaire_id)


@dataclass(frozen=True)
class CompteDTO:
    """Représentation d'un compte utilisateur."""

    id: str
    bar_id: str
    user_id: str
    capacites: frozenset[str]

    @classmethod
    def depuis_compte(cls, compte: Compte) -> CompteDTO:
        return cls(
            id=compte.id,
            bar_id=compte.bar_id,
            user_id=compte.user_id,
            capacites=compte.capacites,
        )
