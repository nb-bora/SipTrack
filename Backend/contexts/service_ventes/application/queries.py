"""Côté lecture (CQRS) du contexte Service & Ventes.

Les vues de lecture ne passent **pas** par les agrégats : charger toutes les
ventes dans l'agrégat `Addition` pour en calculer le total contredirait
l'ADR-0004 (petits agrégats, référence par identité). On expose donc un port de
lecture dédié, implémenté en infrastructure.

Le total d'une addition est **calculé, jamais stocké** : le journal des faits
est la seule vérité, tous les états s'en déduisent. Un total persisté serait un
état capable de diverger de ses faits — précisément ce que l'outil doit rendre
impossible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LigneAdditionDTO:
    """Une consommation rattachée à l'addition."""

    vente_id: str
    produit_id: str
    quantite: int
    prix_unitaire: int
    montant_total: int
    forme_paiement: str
    horodatage: str


@dataclass(frozen=True)
class PaiementLigneDTO:
    """Un encaissement porté à cette addition."""

    paiement_id: str
    montant: int
    forme_paiement: str
    horodatage: str


@dataclass(frozen=True)
class AdditionDetailDTO:
    """L'addition telle qu'elle est présentée à la table : ses lignes et son dû.

    `total`, `paye` et `reste_a_payer` sont tous **calculés** à la lecture.
    """

    id: str
    service_id: str
    table_numero: int
    statut: str
    ouvert_le: str
    lignes: tuple[LigneAdditionDTO, ...]
    total: int
    paiements: tuple[PaiementLigneDTO, ...]
    paye: int
    reste_a_payer: int
    ferme_le: str | None = None


@dataclass(frozen=True)
class SousCaisseDTO:
    """Ce qu'une serveuse doit, ce qu'elle a remis, et l'ecart."""

    serveuse_id: str
    encaisse_especes: int
    encaisse_mobile_money: int
    verse: int | None
    ecart: int | None


class SousCaisseQueryService(Protocol):
    def par_service(self, service_id: str) -> tuple[SousCaisseDTO, ...]: ...


class AdditionQueryService(Protocol):
    def detail(self, *, service_id: str, addition_id: str) -> AdditionDetailDTO | None: ...
