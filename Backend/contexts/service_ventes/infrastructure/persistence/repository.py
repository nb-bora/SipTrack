"""Implémentation Django du ServiceRepository."""

from __future__ import annotations

from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.infrastructure.django_app.models import ServiceModel
from contexts.service_ventes.infrastructure.persistence import mapper


class DjangoServiceRepository:
    def ajouter(self, service: Service) -> None:
        ServiceModel.objects.create(**mapper.vers_ligne(service))

    def par_id(self, service_id: str) -> Service | None:
        try:
            ligne = ServiceModel.objects.get(pk=service_id)
        except ServiceModel.DoesNotExist:
            return None
        return mapper.vers_domaine(ligne)
