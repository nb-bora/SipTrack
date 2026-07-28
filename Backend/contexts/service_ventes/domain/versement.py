"""Agrégat racine : Versement.

La recette qu'une serveuse remet à la fin de son service. Petit agrégat
(cf. ADR-0004) qui référence son service et son auteur par identifiant.

C'est ici que se joue la première des deux réconciliations emboîtées du modèle
métier (§9) : **par serveuse, sur l'argent**. On confronte ce qu'elle a encaissé
en espèces à ce qu'elle remet, et l'écart — s'il existe — devient un Fait.
"""

from __future__ import annotations

from datetime import datetime

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.domain.money import Montant

from .events import EcartConstate, RecetteVersee


class Versement:
    def __init__(
        self,
        *,
        id: str,
        service_id: str,
        serveuse_id: str,
        attendu: Montant,
        verse: Montant,
        horodatage: datetime,
    ) -> None:
        self.id = id
        self.service_id = service_id
        self.serveuse_id = serveuse_id
        self.attendu = attendu
        self.verse = verse
        self.horodatage = horodatage
        self._evenements: list[DomainEvent] = []

    @property
    def ecart(self) -> int:
        """Positif : elle remet plus que prévu. Négatif : il manque."""
        return self.verse.valeur - self.attendu.valeur

    @classmethod
    def remettre(
        cls,
        *,
        service_id: str,
        serveuse_id: str,
        attendu: Montant,
        verse: Montant,
        horodatage: datetime,
    ) -> Versement:
        """Enregistre la remise, et l'écart s'il y en a un.

        L'écart n'est jamais absorbé en silence, même d'un franc : le modèle
        métier pose « zéro inexpliqué », sans seuil de tolérance (invariant 4).
        Une caissière honnête est protégée par la trace, pas par l'indulgence.
        """
        versement = cls(
            id=new_id(),
            service_id=service_id,
            serveuse_id=serveuse_id,
            attendu=attendu,
            verse=verse,
            horodatage=horodatage,
        )
        versement._enregistrer(
            RecetteVersee(
                versement_id=versement.id,
                service_id=service_id,
                serveuse_id=serveuse_id,
                attendu=attendu.valeur,
                verse=verse.valeur,
                auteur_id=serveuse_id,
            )
        )
        if versement.ecart != 0:
            versement._enregistrer(
                EcartConstate(
                    versement_id=versement.id,
                    service_id=service_id,
                    serveuse_id=serveuse_id,
                    ecart=versement.ecart,
                    auteur_id=serveuse_id,
                )
            )
        return versement

    def _enregistrer(self, evenement: DomainEvent) -> None:
        self._evenements.append(evenement)

    def evenements_non_publies(self) -> tuple[DomainEvent, ...]:
        return tuple(self._evenements)

    def purger_evenements(self) -> None:
        self._evenements.clear()
