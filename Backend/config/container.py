"""Composition Root.

Unique endroit où les adaptateurs concrets (infrastructure) sont branchés sur
les ports du domaine/application. C'est ce qui réalise l'inversion de
dépendances : la couche interface demande un cas d'usage au conteneur sans jamais
connaître l'infrastructure.

Les imports sont différés (dans les méthodes) pour éviter de charger les modèles
ORM avant que les applications Django ne soient prêtes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contexts.service_ventes.application.dto import ServiceDTO
    from contexts.service_ventes.application.use_cases.ouvrir_service import (
        OuvrirServiceHandler,
    )


class SystemClock:
    """Implémentation par défaut du port Clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class Container:
    """Fabrique de cas d'usage câblés avec l'infrastructure concrète."""

    def ouvrir_service(self) -> OuvrirServiceHandler:
        from contexts.service_ventes.application.use_cases.ouvrir_service import (
            OuvrirServiceHandler,
        )
        from contexts.service_ventes.infrastructure.journal.journal import DjangoJournal
        from contexts.service_ventes.infrastructure.persistence.repository import (
            DjangoServiceRepository,
        )
        from contexts.service_ventes.infrastructure.unit_of_work import DjangoUnitOfWork

        return OuvrirServiceHandler(
            uow=DjangoUnitOfWork(),
            services=DjangoServiceRepository(),
            journal=DjangoJournal(),
            clock=SystemClock(),
        )

    def service_par_id(self, service_id: str) -> ServiceDTO | None:
        from contexts.service_ventes.application.dto import ServiceDTO
        from contexts.service_ventes.infrastructure.persistence.repository import (
            DjangoServiceRepository,
        )

        service = DjangoServiceRepository().par_id(service_id)
        return ServiceDTO.depuis(service) if service is not None else None


container = Container()
