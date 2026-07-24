"""Port de persistance : ServiceRepository.

L'interface appartient au domaine (concept du langage ubiquitaire, une par racine
d'agrégat). L'implémentation concrète vit en infrastructure.
"""

from __future__ import annotations

from typing import Protocol

from .service import Service


class ServiceRepository(Protocol):
    def ajouter(self, service: Service) -> None: ...

    def par_id(self, service_id: str) -> Service | None: ...
