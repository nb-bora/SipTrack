"""Fixtures et fakes du contexte Crédit & Créances."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from types import TracebackType

from rest_framework.test import APIClient

from contexts.credit_creances.domain.client import Client
from contexts.credit_creances.domain.credit import Credit
from contexts.credit_creances.domain.remboursement import Remboursement
from shared.domain.events import DomainEvent

INSTANT_TEST = datetime(2026, 7, 28, 22, 0, tzinfo=UTC)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rolled_back = True

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakeClock:
    def __init__(self, instant: datetime = INSTANT_TEST) -> None:
        self.instant = instant

    def now(self) -> datetime:
        return self.instant


class FakeJournal:
    def __init__(self) -> None:
        self.appels: list[tuple[tuple[DomainEvent, ...], str]] = []

    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None:
        self.appels.append((tuple(evenements), auteur_id))

    def evenements(self) -> list[DomainEvent]:
        return [evt for lot, _ in self.appels for evt in lot]


class FakeClientRepository:
    def __init__(self, clients: list[Client] | None = None) -> None:
        self.ajoutes: list[Client] = []
        self._clients = clients or []

    def ajouter(self, client: Client) -> None:
        self.ajoutes.append(client)

    def par_id(self, client_id: str) -> Client | None:
        return next((c for c in self._clients + self.ajoutes if c.id == client_id), None)

    def par_bar_et_nom(self, *, bar_id: str, nom: str) -> Client | None:
        return next(
            (c for c in self._clients + self.ajoutes if c.bar_id == bar_id and c.nom == nom),
            None,
        )


class FakeCreditRepository:
    def __init__(self, credits: list[Credit] | None = None) -> None:
        self.ajoutes: list[Credit] = []
        self.mis_a_jour: list[Credit] = []
        self._credits = credits or []

    def ajouter(self, credit: Credit) -> None:
        self.ajoutes.append(credit)

    def par_id(self, credit_id: str) -> Credit | None:
        return next((c for c in self._credits + self.ajoutes if c.id == credit_id), None)

    def par_addition(self, addition_id: str) -> Credit | None:
        return next(
            (c for c in self._credits + self.ajoutes if c.addition_id == addition_id),
            None,
        )

    def mettre_a_jour(self, credit: Credit) -> None:
        self.mis_a_jour.append(credit)


class FakeRemboursementRepository:
    def __init__(self, deja_rembourse: dict[str, int] | None = None) -> None:
        self.ajoutes: list[Remboursement] = []
        self._deja = deja_rembourse or {}

    def ajouter(self, remboursement: Remboursement) -> None:
        self.ajoutes.append(remboursement)

    def total_rembourse(self, credit_id: str) -> int:
        depuis_ajouts = sum(r.montant.valeur for r in self.ajoutes if r.credit_id == credit_id)
        return self._deja.get(credit_id, 0) + depuis_ajouts


def creer_client_via_api(client: APIClient, *, bar_id: str = "bar1", nom: str = "Jean") -> str:
    """Enregistre un client par l'API et renvoie son id."""
    reponse = client.post("/api/clients/", {"bar_id": bar_id, "nom": nom}, format="json")
    assert reponse.status_code == 201
    client_id: str = reponse.json()["id"]
    return client_id
