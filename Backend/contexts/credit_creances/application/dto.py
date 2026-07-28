"""Objets de transfert de données du contexte Crédit & Créances."""

from __future__ import annotations

from dataclasses import dataclass

from contexts.credit_creances.domain.client import Client
from contexts.credit_creances.domain.credit import Credit


@dataclass(frozen=True)
class CreerClientCommand:
    bar_id: str
    nom: str


@dataclass(frozen=True)
class AccorderCreditCommand:
    client_id: str
    service_id: str
    addition_id: str
    montant: int
    auteur_id: str


@dataclass(frozen=True)
class EnregistrerRemboursementCommand:
    credit_id: str
    montant: int
    auteur_id: str


@dataclass(frozen=True)
class ClientDTO:
    id: str
    bar_id: str
    nom: str

    @classmethod
    def depuis(cls, client: Client) -> ClientDTO:
        return cls(id=client.id, bar_id=client.bar_id, nom=client.nom)


@dataclass(frozen=True)
class CreditDTO:
    id: str
    client_id: str
    service_id: str
    addition_id: str
    montant: int
    rembourse: int
    reste: int
    statut: str

    @classmethod
    def depuis(cls, credit: Credit, *, rembourse: int) -> CreditDTO:
        return cls(
            id=credit.id,
            client_id=credit.client_id,
            service_id=credit.service_id,
            addition_id=credit.addition_id,
            montant=credit.montant.valeur,
            rembourse=rembourse,
            reste=credit.montant.valeur - rembourse,
            statut=str(credit.statut),
        )
