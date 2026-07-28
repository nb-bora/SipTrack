"""Événements de domaine du contexte Gouvernance & Accès.

Chaque changement de droit, chaque création de bar, chaque délégation s'écrit
comme un Fait immuable — sinon la question « qui pouvait faire ça ? » reste sans
réponse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class BarCree(DomainEvent):
    """Un bar rejoint la plateforme avec un propriétaire."""

    bar_id: str
    nom: str
    proprietaire_id: str


@dataclass(frozen=True, kw_only=True)
class CompteCree(DomainEvent):
    """Un utilisateur se voit rattacher à un bar avec des capacités initiales."""

    compte_id: str
    bar_id: str
    user_id: str
    # Les capacites initiales, jamais auto-declarees. Une gerance ne peut pas
    # creer un compte avec des droits qu'il n'a pas lui-meme.
    # Stored as tuple pour être JSON seriable (frozenset ne passe pas)
    capacites_initiales: tuple[str, ...]
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class CapaciteAccordee(DomainEvent):
    """Une capacité atomique est accordée à un compte."""

    compte_id: str
    bar_id: str
    capacite: str
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class CapaciteRetiree(DomainEvent):
    """Une capacité est retirée — une correction, jamais un oubli."""

    compte_id: str
    bar_id: str
    capacite: str
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class RoleCompose(DomainEvent):
    """Un rôle est créé par composition de capacités atomiques.

    Nommé en métier (« encaisser »), jamais en technique. Permet à une gérante
    de lire ses propres réglages sans connaître l'API.
    """

    role_id: str
    bar_id: str
    nom: str
    capacites: frozenset[str]
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class DelegationAccordee(DomainEvent):
    """Une personne se voit déléguer temporairement un rôle ou une capacité.

    Datée et révocable — « ce soir, Marie supervise » s'écrit, s'évalue, s'oublie.
    """

    delegation_id: str
    bar_id: str
    compte_id: str
    # Peut etre un role_id ou une capacite
    quoi: str
    debut: datetime
    fin: datetime | None  # None = « jusqu'a revocation »
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class DelegationRetiree(DomainEvent):
    """Une délégation prend fin avant son terme."""

    delegation_id: str
    bar_id: str
    compte_id: str
    auteur_id: str
