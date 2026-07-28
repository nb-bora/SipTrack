"""Agrégat Compte — un utilisateur dans un bar, avec ses capacités.

Chaque modification de capacité s'écrit comme un Fait — jamais de simple mutation
d'état. Ça garantit que la question « qui pouvait faire ça ? » a toujours une
réponse traçable.
"""

from __future__ import annotations

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id

from .enums import CapaciteAtomique
from .events import CapaciteAccordee, CapaciteRetiree, CompteCree
from .exceptions import (
    CapaciteDejaAccordée,
    CapaciteNonAccordée,
    CapaciteRequiseManquante,
)


class Compte:
    """Agregat : un utilisateur rattaché à un bar.

    Porte les capacites qui lui ont ete accordees — jamais auto-declarees.
    Chaque changement est un Fait journalise.
    """

    def __init__(
        self,
        *,
        id: str,
        bar_id: str,
        user_id: str,
        capacites: frozenset[str],
    ) -> None:
        self.id = id
        self.bar_id = bar_id
        self.user_id = user_id
        self.capacites = capacites
        self._evenements: list[DomainEvent] = []

    @classmethod
    def creer(
        cls,
        *,
        bar_id: str,
        user_id: str,
        capacites_initiales: frozenset[str],
        auteur_id: str,
    ) -> Compte:
        """Crée un compte avec des capacités initiales.

        Les capacites ne peuvent etre accordees que par quelqu'un qui les
        possède. Cette logique est dans le cas d'usage, pas ici.
        """
        compte = cls(
            id=new_id(),
            bar_id=bar_id,
            user_id=user_id,
            capacites=capacites_initiales,
        )
        compte._enregistrer(
            CompteCree(
                compte_id=compte.id,
                bar_id=bar_id,
                user_id=user_id,
                capacites_initiales=tuple(sorted(capacites_initiales)),
                auteur_id=auteur_id,
            )
        )
        return compte

    def accorder(self, *, capacite: str, auteur_id: str) -> None:
        """Accorde une capacité atomique.

        Levée si déjà accordée. Le refus vient d'ici (métier), pas du
        middleware d'autorisation.
        """
        if not CapaciteAtomique.valide(capacite):
            raise ValueError(f"Capacité inconnue : {capacite}")

        if capacite in self.capacites:
            raise CapaciteDejaAccordée(self.id, capacite)

        self.capacites = self.capacites | {capacite}
        self._enregistrer(
            CapaciteAccordee(
                compte_id=self.id,
                bar_id=self.bar_id,
                capacite=capacite,
                auteur_id=auteur_id,
            )
        )

    def retirer(self, *, capacite: str, auteur_id: str) -> None:
        """Retire une capacité.

        Levée si non accordée. Un retrait sans raison valide est un acte
        douteux — le système refuse la non-opération.
        """
        if not CapaciteAtomique.valide(capacite):
            raise ValueError(f"Capacité inconnue : {capacite}")

        if capacite not in self.capacites:
            raise CapaciteNonAccordée(self.id, capacite)

        self.capacites = self.capacites - {capacite}
        self._enregistrer(
            CapaciteRetiree(
                compte_id=self.id,
                bar_id=self.bar_id,
                capacite=capacite,
                auteur_id=auteur_id,
            )
        )

    def possede(self, capacite: str) -> bool:
        """Vérifie qu'une capacité est accordée."""
        return capacite in self.capacites

    def verifier_capacite(self, capacite: str, operation: str) -> None:
        """Lève si la capacité requise manque.

        Point d'entrée du système d'autorisation au niveau métier.
        """
        if not self.possede(capacite):
            raise CapaciteRequiseManquante(self.id, capacite, operation)

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
