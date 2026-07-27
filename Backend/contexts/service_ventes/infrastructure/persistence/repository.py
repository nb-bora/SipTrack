"""Implémentation Django du ServiceRepository, VenteRepository, AdditionRepository."""

from __future__ import annotations

from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.domain.vente import Vente
from contexts.service_ventes.infrastructure.django_app.models import (
    AdditionModel,
    ServiceModel,
    VenteModel,
)
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

    def mettre_a_jour(self, service: Service) -> None:
        data = mapper.vers_ligne(service)
        ServiceModel.objects.filter(pk=service.id).update(**data)


class DjangoVenteRepository:
    def ajouter(self, vente: Vente) -> None:
        VenteModel.objects.create(**mapper.vers_ligne_vente(vente))


class DjangoAdditionRepository:
    def ajouter(self, addition: Addition) -> None:
        AdditionModel.objects.create(**mapper.vers_ligne_addition(addition))

    def par_id(self, addition_id: str) -> Addition | None:
        try:
            ligne = AdditionModel.objects.get(pk=addition_id)
        except AdditionModel.DoesNotExist:
            return None
        return mapper.vers_domaine_addition(ligne)
