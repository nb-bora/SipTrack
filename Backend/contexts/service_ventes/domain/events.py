"""Événements de domaine du contexte Service & Ventes."""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ServiceOuvert(DomainEvent):
    service_id: str
    bar_id: str
    auteur_id: str
    fond_de_caisse: int


@dataclass(frozen=True, kw_only=True)
class VenteEnregistree(DomainEvent):
    vente_id: str
    service_id: str
    produit_id: str
    quantite: int
    prix_unitaire: int
    montant_total: int
    forme_paiement: str
    auteur_id: str
    addition_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class ServiceCloture(DomainEvent):
    service_id: str
    bar_id: str
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class AdditionOuverte(DomainEvent):
    addition_id: str
    service_id: str
    table_numero: int
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class PaiementRecu(DomainEvent):
    paiement_id: str
    addition_id: str
    service_id: str
    montant: int
    forme_paiement: str
    auteur_id: str


@dataclass(frozen=True, kw_only=True)
class AdditionReglee(DomainEvent):
    addition_id: str
    service_id: str
    table_numero: int
    auteur_id: str
