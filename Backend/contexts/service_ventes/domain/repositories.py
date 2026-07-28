"""Port de persistance : ServiceRepository, VenteRepository, AdditionRepository.

L'interface appartient au domaine (concept du langage ubiquitaire, une par racine
d'agrégat). L'implémentation concrète vit en infrastructure.
"""

from __future__ import annotations

from typing import Protocol

from .addition import Addition
from .service import Service
from .vente import Vente


class ServiceRepository(Protocol):
    def ajouter(self, service: Service) -> None: ...

    def par_id(self, service_id: str) -> Service | None: ...

    def mettre_a_jour(self, service: Service) -> None: ...


class VenteRepository(Protocol):
    def ajouter(self, vente: Vente) -> None: ...


class AdditionRepository(Protocol):
    def ajouter(self, addition: Addition) -> None: ...

    def par_id(self, addition_id: str) -> Addition | None: ...

    def mettre_a_jour(self, addition: Addition) -> None: ...

    def compter_ouvertes(self, service_id: str) -> int:
        """Combien de tables attendent encore leur règlement sur ce service."""
        ...
