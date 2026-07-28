"""Implémentation Django du ServiceRepository, VenteRepository, AdditionRepository."""

from __future__ import annotations

from django.db.models import Sum

from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.enums import StatutAddition
from contexts.service_ventes.domain.paiement import Paiement
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.domain.vente import Vente
from contexts.service_ventes.infrastructure.django_app.models import (
    AdditionModel,
    PaiementModel,
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

    def total_addition(self, addition_id: str) -> int:
        total = VenteModel.objects.filter(addition_id=addition_id).aggregate(
            somme=Sum("montant_total")
        )["somme"]
        return int(total or 0)


class DjangoPaiementRepository:
    def ajouter(self, paiement: Paiement) -> None:
        PaiementModel.objects.create(**mapper.vers_ligne_paiement(paiement))

    def total_encaisse(self, addition_id: str) -> int:
        total = PaiementModel.objects.filter(addition_id=addition_id).aggregate(
            somme=Sum("montant")
        )["somme"]
        return int(total or 0)


class DjangoAdditionRepository:
    def ajouter(self, addition: Addition) -> None:
        AdditionModel.objects.create(**mapper.vers_ligne_addition(addition))

    def par_id(self, addition_id: str) -> Addition | None:
        try:
            ligne = AdditionModel.objects.get(pk=addition_id)
        except AdditionModel.DoesNotExist:
            return None
        return mapper.vers_domaine_addition(ligne)

    def mettre_a_jour(self, addition: Addition) -> None:
        data = mapper.vers_ligne_addition(addition)
        AdditionModel.objects.filter(pk=addition.id).update(**data)

    def compter_ouvertes(self, service_id: str) -> int:
        return AdditionModel.objects.filter(
            service_id=service_id,
            statut=StatutAddition.OUVERTE.value,
        ).count()
