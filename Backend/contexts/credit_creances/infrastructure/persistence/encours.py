"""Lecture des encours : qui doit quoi, calculé à la lecture."""

from __future__ import annotations

from django.db.models import Sum

from contexts.credit_creances.application.queries import CreanceDTO, EncoursClientDTO
from contexts.credit_creances.domain.enums import StatutCredit
from contexts.credit_creances.infrastructure.django_app.models import (
    ClientModel,
    CreditModel,
)


class DjangoEncoursQueryService:
    def par_client(self, client_id: str) -> EncoursClientDTO | None:
        client = ClientModel.objects.filter(id=client_id).first()
        if client is None:
            return None
        return self._encours(client)

    def tous(self, bar_id: str) -> tuple[EncoursClientDTO, ...]:
        encours = (
            self._encours(client)
            for client in ClientModel.objects.filter(bar_id=bar_id).order_by("nom")
        )
        # Un client sans dette en cours n'a rien à faire dans une liste de dettes.
        return tuple(e for e in encours if e.reste > 0)

    def _encours(self, client: ClientModel) -> EncoursClientDTO:
        dettes = CreditModel.objects.filter(client_id=client.id).annotate(
            total_rembourse=Sum("remboursements__montant")
        )

        creances = tuple(
            CreanceDTO(
                credit_id=credit.id,
                client_id=client.id,
                client_nom=client.nom,
                service_id=credit.service_id,
                addition_id=credit.addition_id,
                montant=credit.montant,
                rembourse=int(credit.total_rembourse or 0),
                reste=credit.montant - int(credit.total_rembourse or 0),
                statut=credit.statut,
            )
            for credit in dettes
        )

        return EncoursClientDTO(
            client_id=client.id,
            client_nom=client.nom,
            total_du=sum(c.montant for c in creances),
            total_rembourse=sum(c.rembourse for c in creances),
            reste=sum(c.reste for c in creances if c.statut != str(StatutCredit.SOLDE)),
            creances=creances,
        )
