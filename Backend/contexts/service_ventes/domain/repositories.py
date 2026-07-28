"""Port de persistance : ServiceRepository, VenteRepository, AdditionRepository.

L'interface appartient au domaine (concept du langage ubiquitaire, une par racine
d'agrégat). L'implémentation concrète vit en infrastructure.
"""

from __future__ import annotations

from typing import Protocol

from .addition import Addition
from .paiement import Paiement
from .service import Service
from .vente import Vente
from .versement import Versement


class ServiceRepository(Protocol):
    def ajouter(self, service: Service) -> None: ...

    def par_id(self, service_id: str) -> Service | None: ...

    def mettre_a_jour(self, service: Service) -> None: ...


class VenteRepository(Protocol):
    def ajouter(self, vente: Vente) -> None: ...

    def total_addition(self, addition_id: str) -> int:
        """Somme des consommations rattachées à cette addition."""
        ...


class AdditionRepository(Protocol):
    def ajouter(self, addition: Addition) -> None: ...

    def par_id(self, addition_id: str) -> Addition | None: ...

    def mettre_a_jour(self, addition: Addition) -> None: ...

    def compter_ouvertes(self, service_id: str) -> int:
        """Combien de tables attendent encore leur règlement sur ce service."""
        ...


class PaiementRepository(Protocol):
    def ajouter(self, paiement: Paiement) -> None: ...

    def total_encaisse(self, addition_id: str) -> int:
        """Somme déjà encaissée sur cette addition."""
        ...

    def especes_encaissees_par(self, *, service_id: str, auteur_id: str) -> int:
        """Espèces encaissées par cette personne sur ce service.

        Seules les espèces : le mobile money ne se remet pas de la main à la
        main, il n'a rien à faire dans ce qu'une serveuse doit rapporter.
        """
        ...


class VersementRepository(Protocol):
    def ajouter(self, versement: Versement) -> None: ...

    def existe_pour(self, *, service_id: str, serveuse_id: str) -> bool: ...
