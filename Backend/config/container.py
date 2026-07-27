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
    from contexts.service_ventes.application.use_cases.cloturer_service import (
        CloturerServiceHandler,
    )
    from contexts.service_ventes.application.use_cases.enregistrer_vente import (
        EnregistrerVenteHandler,
    )
    from contexts.service_ventes.application.use_cases.ouvrir_addition import (
        OuvrirAdditionHandler,
    )
    from contexts.service_ventes.application.use_cases.ouvrir_service import (
        OuvrirServiceHandler,
    )
    from contexts.service_ventes.application.use_cases.regler_addition import (
        ReglementAdditionHandler,
    )
    from contexts.service_ventes.domain.repositories import (
        AdditionRepository,
        ServiceRepository,
        VenteRepository,
    )
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
        self._ventes: VenteRepository | None = None
        self._additions: AdditionRepository | None = None
        self._journal: Journal | None = None

    def _service_repository(self) -> ServiceRepository:
        if self._services is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoServiceRepository,
            )

            self._services = DjangoServiceRepository()
        return self._services

    def _vente_repository(self) -> VenteRepository:
        if self._ventes is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoVenteRepository,
            )

            self._ventes = DjangoVenteRepository()
        return self._ventes

    def _addition_repository(self) -> AdditionRepository:
        if self._additions is None:
            from contexts.service_ventes.infrastructure.persistence.repository import (
                DjangoAdditionRepository,
            )

            self._additions = DjangoAdditionRepository()
        return self._additions

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

    def enregistrer_vente(self) -> EnregistrerVenteHandler:
        from contexts.service_ventes.application.use_cases.enregistrer_vente import (
            EnregistrerVenteHandler,
        )
        from contexts.service_ventes.infrastructure.unit_of_work import DjangoUnitOfWork

        return EnregistrerVenteHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            ventes=self._vente_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def cloturer_service(self) -> CloturerServiceHandler:
        from contexts.service_ventes.application.use_cases.cloturer_service import (
            CloturerServiceHandler,
        )
        from contexts.service_ventes.infrastructure.unit_of_work import DjangoUnitOfWork

        return CloturerServiceHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def ouvrir_addition(self) -> OuvrirAdditionHandler:
        from contexts.service_ventes.application.use_cases.ouvrir_addition import (
            OuvrirAdditionHandler,
        )
        from contexts.service_ventes.infrastructure.unit_of_work import DjangoUnitOfWork

        return OuvrirAdditionHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            services=self._service_repository(),
            additions=self._addition_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def regler_addition(self) -> ReglementAdditionHandler:
        from contexts.service_ventes.application.use_cases.regler_addition import (
            ReglementAdditionHandler,
        )
        from contexts.service_ventes.infrastructure.unit_of_work import DjangoUnitOfWork

        return ReglementAdditionHandler(
            uow=DjangoUnitOfWork(),  # fraîche à chaque appel (transaction)
            additions=self._addition_repository(),
            journal=self._journal_adapter(),
            clock=self._clock,
        )

    def service_par_id(self, service_id: str) -> ServiceDTO | None:
        from contexts.service_ventes.application.dto import ServiceDTO

        service = self._service_repository().par_id(service_id)
        return ServiceDTO.depuis(service) if service is not None else None


container = Container()
