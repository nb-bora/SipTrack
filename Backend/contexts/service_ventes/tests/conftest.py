"""Fixtures et fakes partagés entre tous les tests du contexte Service & Ventes."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from types import TracebackType
from uuid import uuid4

from rest_framework.test import APIClient

from contexts.service_ventes.application.ports import ArticleVendable
from contexts.service_ventes.domain.addition import Addition
from contexts.service_ventes.domain.enums import FormePaiement, StatutAddition
from contexts.service_ventes.domain.exceptions import ClientInconnu, ProduitNonVendable
from contexts.service_ventes.domain.paiement import Paiement
from contexts.service_ventes.domain.service import Service
from contexts.service_ventes.domain.vente import Vente
from shared.domain.attribution import Attribution, Capacite
from shared.domain.events import DomainEvent
from shared.domain.money import Montant

INSTANT_TEST = datetime(2026, 7, 24, 17, 0, tzinfo=UTC)


class FakeUnitOfWork:
    """Implémentation fake du port UnitOfWork pour les tests."""

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


class FakeServiceRepository:
    """Implémentation fake du ServiceRepository pour les tests."""

    def __init__(self, service: Service | None = None) -> None:
        self.ajoutes: list[Service] = []
        self.mises_a_jour: list[Service] = []
        self._service = service

    def ajouter(self, service: Service) -> None:
        self.ajoutes.append(service)

    def par_id(self, service_id: str) -> Service | None:
        if self._service is not None:
            return self._service
        return next((s for s in self.ajoutes if s.id == service_id), None)

    def mettre_a_jour(self, service: Service) -> None:
        self.mises_a_jour.append(service)
        # Simule aussi une mise à jour locale
        for i, s in enumerate(self.ajoutes):
            if s.id == service.id:
                self.ajoutes[i] = service
                break


class FakeJournal:
    """Implémentation fake du port Journal pour les tests."""

    def __init__(self) -> None:
        self.appels: list[tuple[tuple[DomainEvent, ...], str]] = []
        self.mouvements: list[dict[str, object]] = []

    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None:
        self.appels.append((tuple(evenements), auteur_id))
        for evt in evenements:
            self.mouvements.append(
                {
                    "type": evt.__class__.__name__,
                    **evt.__dict__,
                }
            )


class FakeAdditionRepository:
    """Implémentation fake du AdditionRepository pour les tests."""

    def __init__(self, additions: list[Addition] | None = None) -> None:
        self.ajoutes: list[Addition] = []
        self.mises_a_jour: list[Addition] = []
        self._additions = additions or []

    def ajouter(self, addition: Addition) -> None:
        self.ajoutes.append(addition)

    def par_id(self, addition_id: str) -> Addition | None:
        for add in self._additions + self.ajoutes:
            if add.id == addition_id:
                return add
        return None

    def mettre_a_jour(self, addition: Addition) -> None:
        self.mises_a_jour.append(addition)
        for i, add in enumerate(self._additions):
            if add.id == addition.id:
                self._additions[i] = addition
                break
        for i, add in enumerate(self.ajoutes):
            if add.id == addition.id:
                self.ajoutes[i] = addition
                break

    def compter_ouvertes(self, service_id: str) -> int:
        return sum(
            1
            for add in self._additions + self.ajoutes
            if add.service_id == service_id and add.statut is StatutAddition.OUVERTE
        )


class FakeVenteRepository:
    """Implémentation fake du VenteRepository pour les tests."""

    def __init__(self, totaux_par_addition: dict[str, int] | None = None) -> None:
        self.ajoutes: list[Vente] = []
        self._totaux = totaux_par_addition or {}

    def ajouter(self, vente: Vente) -> None:
        self.ajoutes.append(vente)

    def total_addition(self, addition_id: str) -> int:
        return self._totaux.get(addition_id, 0)


class FakePaiementRepository:
    """Implémentation fake du PaiementRepository pour les tests."""

    def __init__(self, deja_encaisse: dict[str, int] | None = None) -> None:
        self.ajoutes: list[Paiement] = []
        self._deja_encaisse = deja_encaisse or {}

    def ajouter(self, paiement: Paiement) -> None:
        self.ajoutes.append(paiement)

    def total_encaisse(self, addition_id: str) -> int:
        depuis_les_ajouts = sum(
            p.montant.valeur for p in self.ajoutes if p.addition_id == addition_id
        )
        return self._deja_encaisse.get(addition_id, 0) + depuis_les_ajouts

    def especes_encaissees_par(self, *, service_id: str, auteur_id: str) -> int:
        return sum(
            p.montant.valeur
            for p in self.ajoutes
            if p.service_id == service_id
            and p.auteur_id == auteur_id
            and p.forme_paiement is FormePaiement.ESPECES
        )


class FakeTarifs:
    """Implémentation fake du port TarifDuProduit pour les tests.

    Par défaut, tout produit vaut `prix_par_defaut` : les tests qui ne parlent
    pas de prix n'ont pas à monter un catalogue.
    """

    def __init__(
        self,
        prix: dict[str, int] | None = None,
        *,
        prix_par_defaut: int = 1_000,
        retires: set[str] | None = None,
    ) -> None:
        self._prix = prix or {}
        self._prix_par_defaut = prix_par_defaut
        self._retires = retires or set()
        self.demandes: list[tuple[str, str]] = []

    def prix_de(self, *, produit_id: str, bar_id: str) -> ArticleVendable:
        self.demandes.append((produit_id, bar_id))
        if produit_id in self._retires:
            raise ProduitNonVendable(produit_id, "retiré de la vente")
        return ArticleVendable(
            produit_id=produit_id,
            prix_unitaire=self._prix.get(produit_id, self._prix_par_defaut),
        )


class FakeCreances:
    """Implémentation fake du port OuvertureDeCreance pour les tests.

    Enregistre les créances ouvertes pour qu'un test puisse vérifier qu'un
    crédit encaissé laisse bien une dette derrière lui.
    """

    def __init__(self, clients_connus: set[str] | None = None) -> None:
        self.ouvertes: list[dict[str, object]] = []
        self._clients_connus = clients_connus

    def ouvrir(
        self,
        *,
        client_id: str,
        service_id: str,
        addition_id: str,
        montant: int,
        auteur_id: str,
    ) -> None:
        if self._clients_connus is not None and client_id not in self._clients_connus:
            raise ClientInconnu(client_id)
        self.ouvertes.append(
            {
                "client_id": client_id,
                "service_id": service_id,
                "addition_id": addition_id,
                "montant": montant,
                "auteur_id": auteur_id,
            }
        )


class FakeClock:
    """Implémentation fake du port Clock pour les tests."""

    def __init__(self, instant: datetime = INSTANT_TEST) -> None:
        self.instant = instant
        self.appels = 0

    def now(self) -> datetime:
        self.appels += 1
        return self.instant


class SystemClockFake(FakeClock):
    """Alias pour compatibility avec les tests."""

    pass


def ouvrir_service_via_api(client: APIClient, fond_de_caisse: int = 10_000) -> str:
    """Ouvre un service par l'API et renvoie son id (client déjà authentifié)."""
    reponse = client.post(
        "/api/services/",
        {
            "bar_id": "bar1",
            "capacite": "operatrice",
            "fond_de_caisse": fond_de_caisse,
        },
        format="json",
    )
    assert reponse.status_code == 201
    service_id: str = reponse.json()["id"]
    return service_id


def inscrire_produit_via_api(
    client: APIClient,
    *,
    prix: int,
    bar_id: str = "bar1",
    nom: str | None = None,
) -> str:
    """Inscrit un produit au catalogue et renvoie son id.

    Le prix d'une vente vient désormais du catalogue : un test qui veut vendre
    pour un montant donné inscrit d'abord un produit à ce prix.
    """
    reponse = client.post(
        "/api/produits/",
        {"bar_id": bar_id, "nom": nom or f"produit-{uuid4().hex[:8]}", "prix": prix},
        format="json",
    )
    assert reponse.status_code == 201
    produit_id: str = reponse.json()["id"]
    return produit_id


def ouvrir_addition_via_api(client: APIClient, service_id: str, table_numero: int = 5) -> str:
    """Ouvre une addition par l'API et renvoie son id."""
    reponse = client.post(
        f"/api/services/{service_id}/additions/",
        {"table_numero": table_numero},
        format="json",
    )
    assert reponse.status_code == 201
    addition_id: str = reponse.json()["id"]
    return addition_id


def creer_service_ouvert(instant: datetime = INSTANT_TEST) -> Service:
    """Crée un service dans l'état OUVERT pour les tests."""
    return Service.ouvrir(
        bar_id="bar1",
        responsable=Attribution(auteur_id="g1", capacite=Capacite.OPERATRICE, horodatage=instant),
        fond_de_caisse=Montant(10_000),
        horodatage=instant,
    )
