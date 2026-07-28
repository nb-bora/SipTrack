"""Traduction domaine <-> modèles ORM.

Le mapping explicite est ce qui garde le domaine ignorant de la persistance.
"""

from __future__ import annotations

from typing import Any

from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.enums import StatutAddition, StatutService
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.domain.vente import Vente
from contexts.service_ventes.infrastructure.django_app.models import (
    AdditionModel,
    ServiceModel,
)
from shared.domain.attribution import Attribution, Capacite
from shared.domain.money import Montant


def vers_ligne(service: Service) -> dict[str, Any]:
    """Champs prêts pour ServiceModel.objects.create(**...)."""
    return {
        "id": service.id,
        "bar_id": service.bar_id,
        "responsable_id": service.responsable.auteur_id,
        "responsable_capacite": service.responsable.capacite.value,
        "fond_de_caisse": service.fond_de_caisse.montant,
        "statut": service.statut.value,
        "ouvert_le": service.ouvert_le,
        "clos_le": service.clos_le,
    }


def vers_domaine(ligne: ServiceModel) -> Service:
    return Service(
        id=ligne.id,
        bar_id=ligne.bar_id,
        responsable=Attribution(
            auteur_id=ligne.responsable_id,
            capacite=Capacite(ligne.responsable_capacite),
            horodatage=ligne.ouvert_le,
        ),
        fond_de_caisse=Montant(ligne.fond_de_caisse),
        statut=StatutService(ligne.statut),
        ouvert_le=ligne.ouvert_le,
        clos_le=ligne.clos_le,
    )


def vers_ligne_vente(vente: Vente) -> dict[str, Any]:
    """Champs prêts pour VenteModel.objects.create(**...)."""
    return {
        "id": vente.id,
        "service_id": vente.service_id,
        "addition_id": vente.addition_id,
        "produit_id": vente.produit_id,
        "quantite": vente.quantite,
        "prix_unitaire": vente.prix_unitaire.montant,
        "montant_total": vente.montant_total.montant,
        "forme_paiement": vente.forme_paiement.value,
        "horodatage": vente.horodatage,
    }


def vers_ligne_addition(addition: Addition) -> dict[str, Any]:
    """Champs prêts pour AdditionModel.objects.create(**...)."""
    return {
        "id": addition.id,
        "service_id": addition.service_id,
        "table_numero": addition.table_numero,
        "statut": addition.statut.value,
        "ouvert_le": addition.ouvert_le,
        "ferme_le": addition.ferme_le,
    }


def vers_domaine_addition(ligne: AdditionModel) -> Addition:
    return Addition(
        id=ligne.id,
        service_id=ligne.service_id,
        table_numero=ligne.table_numero,
        statut=StatutAddition(ligne.statut),
        ouvert_le=ligne.ouvert_le,
        ferme_le=ligne.ferme_le,
    )
