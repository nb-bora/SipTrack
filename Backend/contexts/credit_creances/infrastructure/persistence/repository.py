"""Adaptateurs Django des repositories du contexte Crédit & Créances."""

from __future__ import annotations

from django.db.models import Sum

from contexts.credit_creances.domain.client import Client
from contexts.credit_creances.domain.credit import Credit
from contexts.credit_creances.domain.enums import StatutCredit
from contexts.credit_creances.domain.remboursement import Remboursement
from contexts.credit_creances.infrastructure.django_app.models import (
    ClientModel,
    CreditModel,
    RemboursementModel,
)
from shared.domain.money import Montant


def _vers_client(modele: ClientModel) -> Client:
    return Client(id=modele.id, bar_id=modele.bar_id, nom=modele.nom)


def _vers_credit(modele: CreditModel) -> Credit:
    return Credit(
        id=modele.id,
        client_id=modele.client_id,
        service_id=modele.service_id,
        addition_id=modele.addition_id,
        montant=Montant(modele.montant),
        statut=StatutCredit(modele.statut),
        ne_le=modele.ne_le,
    )


class DjangoClientRepository:
    def ajouter(self, client: Client) -> None:
        ClientModel.objects.create(id=client.id, bar_id=client.bar_id, nom=client.nom)

    def par_id(self, client_id: str) -> Client | None:
        modele = ClientModel.objects.filter(id=client_id).first()
        return _vers_client(modele) if modele is not None else None

    def par_bar_et_nom(self, *, bar_id: str, nom: str) -> Client | None:
        modele = ClientModel.objects.filter(bar_id=bar_id, nom=nom).first()
        return _vers_client(modele) if modele is not None else None


class DjangoCreditRepository:
    def ajouter(self, credit: Credit) -> None:
        CreditModel.objects.create(
            id=credit.id,
            client_id=credit.client_id,
            service_id=credit.service_id,
            addition_id=credit.addition_id,
            montant=credit.montant.valeur,
            statut=str(credit.statut),
            ne_le=credit.ne_le,
        )

    def par_id(self, credit_id: str) -> Credit | None:
        modele = CreditModel.objects.filter(id=credit_id).first()
        return _vers_credit(modele) if modele is not None else None

    def par_addition(self, addition_id: str) -> Credit | None:
        modele = CreditModel.objects.filter(addition_id=addition_id).first()
        return _vers_credit(modele) if modele is not None else None

    def mettre_a_jour(self, credit: Credit) -> None:
        CreditModel.objects.filter(id=credit.id).update(statut=str(credit.statut))


class DjangoRemboursementRepository:
    def ajouter(self, remboursement: Remboursement) -> None:
        RemboursementModel.objects.create(
            id=remboursement.id,
            credit_id=remboursement.credit_id,
            client_id=remboursement.client_id,
            montant=remboursement.montant.valeur,
            auteur_id=remboursement.auteur_id,
            horodatage=remboursement.horodatage,
        )

    def total_rembourse(self, credit_id: str) -> int:
        total = RemboursementModel.objects.filter(credit_id=credit_id).aggregate(
            somme=Sum("montant")
        )["somme"]
        return int(total or 0)
