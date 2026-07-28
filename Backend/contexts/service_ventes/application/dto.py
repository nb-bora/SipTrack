"""Objets de transfert (commandes et vues) de la couche application.

Aucun modèle ORM ni agrégat n'est exposé hors des couches internes : on passe
par ces DTO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contexts.service_ventes.domain.addition import Addition
    from contexts.service_ventes.domain.paiement import Paiement
    from contexts.service_ventes.domain.service import Service
    from contexts.service_ventes.domain.vente import Vente
    from contexts.service_ventes.domain.versement import Versement


@dataclass(frozen=True)
class OuvrirServiceCommand:
    bar_id: str
    auteur_id: str
    capacite: str
    fond_de_caisse: int


@dataclass(frozen=True)
class CloturerServiceCommand:
    service_id: str
    auteur_id: str


@dataclass(frozen=True)
class EnregistrerVenteCommand:
    service_id: str
    auteur_id: str
    produit_id: str
    quantite: int
    prix_unitaire: int
    forme_paiement: str
    # Absent pour une vente au comptoir : toutes les consommations ne passent
    # pas par une table.
    addition_id: str | None = None


@dataclass(frozen=True)
class ServiceDTO:
    id: str
    bar_id: str
    statut: str
    fond_de_caisse: int
    ouvert_le: str
    clos_le: str | None = None

    @classmethod
    def depuis(cls, service: Service) -> ServiceDTO:
        return cls(
            id=service.id,
            bar_id=service.bar_id,
            statut=service.statut.value,
            fond_de_caisse=service.fond_de_caisse.valeur,
            ouvert_le=service.ouvert_le.isoformat(),
            clos_le=service.clos_le.isoformat() if service.clos_le is not None else None,
        )


@dataclass(frozen=True)
class AdditionDTO:
    id: str
    service_id: str
    table_numero: int
    statut: str
    ouvert_le: str
    ferme_le: str | None = None

    @classmethod
    def depuis(cls, addition: Addition) -> AdditionDTO:
        return cls(
            id=addition.id,
            service_id=addition.service_id,
            table_numero=addition.table_numero,
            statut=addition.statut.value,
            ouvert_le=addition.ouvert_le.isoformat(),
            ferme_le=addition.ferme_le.isoformat() if addition.ferme_le is not None else None,
        )


@dataclass(frozen=True)
class OuvrirAdditionCommand:
    service_id: str
    auteur_id: str
    table_numero: int


@dataclass(frozen=True)
class ReglementAdditionCommand:
    service_id: str
    addition_id: str
    auteur_id: str


@dataclass(frozen=True)
class EnregistrerPaiementCommand:
    service_id: str
    addition_id: str
    auteur_id: str
    montant: int
    forme_paiement: str
    # Obligatoire pour un crédit uniquement : c'est le débiteur.
    client_id: str = ""


@dataclass(frozen=True)
class PaiementDTO:
    id: str
    addition_id: str
    service_id: str
    montant: int
    forme_paiement: str
    reste_a_payer: int

    @classmethod
    def depuis(cls, paiement: Paiement, *, reste_a_payer: int) -> PaiementDTO:
        return cls(
            id=paiement.id,
            addition_id=paiement.addition_id,
            service_id=paiement.service_id,
            montant=paiement.montant.valeur,
            forme_paiement=paiement.forme_paiement.value,
            reste_a_payer=reste_a_payer,
        )


@dataclass(frozen=True)
class VenteDTO:
    id: str
    service_id: str
    produit_id: str
    quantite: int
    prix_unitaire: int
    montant_total: int
    forme_paiement: str
    addition_id: str | None = None

    @classmethod
    def depuis(cls, vente: Vente) -> VenteDTO:
        return cls(
            id=vente.id,
            service_id=vente.service_id,
            produit_id=vente.produit_id,
            quantite=vente.quantite,
            prix_unitaire=vente.prix_unitaire.valeur,
            montant_total=vente.montant_total.valeur,
            forme_paiement=vente.forme_paiement.value,
            addition_id=vente.addition_id,
        )


@dataclass(frozen=True)
class VerserRecetteCommand:
    service_id: str
    serveuse_id: str
    montant: int


@dataclass(frozen=True)
class VersementDTO:
    id: str
    service_id: str
    serveuse_id: str
    attendu: int
    verse: int
    ecart: int

    @classmethod
    def depuis(cls, versement: Versement) -> VersementDTO:
        return cls(
            id=versement.id,
            service_id=versement.service_id,
            serveuse_id=versement.serveuse_id,
            attendu=versement.attendu.valeur,
            verse=versement.verse.valeur,
            ecart=versement.ecart,
        )
