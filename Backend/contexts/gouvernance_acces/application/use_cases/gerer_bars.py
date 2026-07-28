"""Cas d'usage : créer et lister les bars d'un propriétaire."""

from __future__ import annotations

from contexts.gouvernance_acces.application.dto import BarDTO, CreerBarCommand
from contexts.gouvernance_acces.domain.bar import Bar
from contexts.gouvernance_acces.domain.compte import Compte
from contexts.gouvernance_acces.domain.enums import CapaciteAtomique
from contexts.gouvernance_acces.domain.exceptions import BarDejaExistant
from contexts.gouvernance_acces.domain.repositories import (
    BarRepository,
    CompteRepository,
)
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork


class GererBarsHandler:
    """Créer un bar, le seul acte qui n'exige aucune autorisation préalable.

    C'est l'entrée du système : une personne crée son bar et devient
    automatiquement son propriétaire avec TOUTES les capacités.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        bars: BarRepository,
        comptes: CompteRepository | None = None,
        journal: Journal,
    ) -> None:
        self._uow = uow
        self._bars = bars
        self._comptes = comptes
        self._journal = journal

    def creer(self, commande: CreerBarCommand) -> BarDTO:
        """Crée un bar au nom du propriétaire authentifié.

        Aucun deux bars n'ont le même nom sous le même propriétaire.
        """
        with self._uow:
            # Vérifier qu'aucun bar de ce propriétaire n'a ce nom.
            existants = self._bars.du_proprietaire(commande.proprietaire_id)
            if any(b.nom == commande.nom for b in existants):
                raise BarDejaExistant(commande.nom)

            bar = Bar.creer(
                nom=commande.nom,
                proprietaire_id=commande.proprietaire_id,
            )
            self._bars.ajouter(bar)
            self._journal.enregistrer(
                bar.evenements_non_publies(), auteur_id=commande.proprietaire_id
            )
            bar.purger_evenements()

            # Le propriétaire reçoit automatiquement TOUTES les capacités (bootstrapping).
            if self._comptes is not None:
                compte_proprio = Compte.creer(
                    bar_id=bar.id,
                    user_id=commande.proprietaire_id,
                    capacites_initiales=CapaciteAtomique.toutes(),
                    auteur_id=commande.proprietaire_id,
                )
                self._comptes.ajouter(compte_proprio)
                self._journal.enregistrer(
                    compte_proprio.evenements_non_publies(), auteur_id=commande.proprietaire_id
                )
                compte_proprio.purger_evenements()

            self._uow.commit()

            return BarDTO.depuis_bar(bar)

    def lister(self, proprietaire_id: str) -> tuple[BarDTO, ...]:
        """Liste tous les bars du propriétaire.

        Pas d'authentification requise — l'identité vient du jeton.
        """
        bars = self._bars.du_proprietaire(proprietaire_id)
        return tuple(BarDTO.depuis_bar(b) for b in bars)
