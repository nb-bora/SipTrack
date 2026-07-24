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
    from contexts.service_ventes.domain.repositories import ServiceRepository
    from shared.application.journal import Journal


class SystemClock:
    """Implémentation par défaut du port Clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class Container:
    """Fabrique de cas d'usage câblés avec l'infrastructure concrète.

    Les adaptateurs **sans état** (repository, journal, horloge) sont créés une
    seule fois puis réutilisés. En revanche, l'Unit of Work est **volontairement
    recréée à chaque cas d'usage** : elle porte l'état d'une transaction et ne
    doit jamais être partagée entre deux exécutions.
    """

    def __init__(self) -> None:
        self._clock = SystemClock()
        self._services: ServiceRepository | None = None
        self._journal: Journal | None = None

    def _service_repository(self) -> ServiceRepository:
        if self._services is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoServiceRepository,
            )

            self._services = DjangoServiceRepository()
        return self._services

    def _journal_adapter(self) -> Journal:
        if self._journal is None:
            from contexts.service_ventes.infrastructure.journal.journal import (
                DjangoJournal,
            )

            self._journal = DjangoJournal()
        return self._journal

    def ouvrir_service(self) -> OuvrirServiceHandler:
        from contexts.service_ventes.application.use_cases.ouvrir_service import (
            OuvrirServiceHandler,
        )
        from contexts.service_ventes.infrastructure.unit_of_work import DjangoUnitOfWork

        return OuvrirServiceHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def service_par_id(self, service_id: str) -> ServiceDTO | None:
        from contexts.service_ventes.application.dto import ServiceDTO

        service = self._service_repository().par_id(service_id)
        return ServiceDTO.depuis(service) if service is not None else None


container = Container()
