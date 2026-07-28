"""Agrégat Bar — l'entité racine du cloisonnement.

Un bar est défini par son propriétaire. Tout ce qui se passe dans ce bar ne peut
être vu / modifié que par quelqu'un qui y appartient et qui a les capacités
requises.

C'est la **fondation** de tout le reste.
"""

from __future__ import annotations

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id

from .events import BarCree


class Bar:
    """Agregat racine : un bar avec son proprietaire.

    Ne modele que ce qui est immuable : l'id, le nom, le proprietaire. Les
    comptes qui y travaillent sont des agregats a part (cf. Compte).
    """

    def __init__(
        self,
        *,
        id: str,
        nom: str,
        proprietaire_id: str,
    ) -> None:
        self.id = id
        self.nom = nom
        self.proprietaire_id = proprietaire_id
        self._evenements: list[DomainEvent] = []

    @classmethod
    def creer(cls, *, nom: str, proprietaire_id: str) -> Bar:
        """Crée un bar et enregistre l'événement."""
        bar = cls(id=new_id(), nom=nom, proprietaire_id=proprietaire_id)
        bar._enregistrer(
            BarCree(
                bar_id=bar.id,
                nom=nom,
                proprietaire_id=proprietaire_id,
            )
        )
        return bar

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
