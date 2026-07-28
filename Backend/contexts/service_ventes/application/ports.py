"""Ports sortants de la couche application du contexte Service & Ventes.

Ce que ce contexte attend du monde extérieur, exprimé dans **son** vocabulaire.
Qui répond, et comment, ne le regarde pas (ADR-0005) : c'est la composition root
qui branche un adaptateur derrière chaque port.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ArticleVendable:
    """Ce que Service & Ventes a besoin de savoir d'un produit : son prix."""

    produit_id: str
    prix_unitaire: int


class TarifDuProduit(Protocol):
    """Donner le prix à appliquer à une vente saisie maintenant.

    Le prix ne vient **jamais** de la requête. S'il en venait, la personne qui
    saisit dicterait ce que la consommation a valu : elle pourrait minorer un
    prix, encaisser le vrai, et la réconciliation de fin de service tomberait
    juste — puisqu'elle compare deux chiffres qu'elle a elle-même choisis.
    """

    def prix_de(self, *, produit_id: str, bar_id: str) -> ArticleVendable:
        """Lève si le produit est inconnu, ou retiré de la vente."""
        ...


class OuvertureDeCreance(Protocol):
    """Ouvrir une créance quand une consommation part en crédit.

    Service & Ventes ne sait pas ce qu'est un crédit, ni comment il se rembourse.
    Il sait seulement ceci : une consommation servie sans argent en face doit
    laisser une **dette quelque part**, sans quoi elle s'évapore. Le suivi de
    cette dette est le métier d'un autre contexte.
    """

    def ouvrir(
        self,
        *,
        client_id: str,
        service_id: str,
        addition_id: str,
        montant: int,
        auteur_id: str,
    ) -> None:
        """Ouvre la créance, ou lève si le client n'existe pas."""
        ...
