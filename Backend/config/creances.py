"""Adaptateur : brancher le port « ouvrir une créance » sur le contexte Crédit.

Service & Ventes déclare avoir besoin qu'une dette soit ouverte quelque part
(`OuvertureDeCreance`) ; Crédit & Créances sait le faire. Ni l'un ni l'autre ne
se connaît : ce module, qui appartient à la composition root, est le **seul**
endroit du système autorisé à voir les deux (ADR-0005).

Le jour où un bus d'événements existera, c'est ce fichier qui disparaîtra —
remplacé par un abonnement à `PaiementRecu`. Le reste ne bougera pas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contexts.credit_creances.application.dto import AccorderCreditCommand
from contexts.credit_creances.domain.exceptions import ClientIntrouvable
from contexts.service_ventes.domain.exceptions import ClientInconnu

if TYPE_CHECKING:
    from contexts.credit_creances.application.use_cases.accorder_credit import (
        AccorderCreditHandler,
    )


class CreanceViaContexteCredit:
    """Implémente `OuvertureDeCreance` en déléguant au contexte Crédit."""

    def __init__(self, accorder_credit: AccorderCreditHandler) -> None:
        self._accorder_credit = accorder_credit

    def ouvrir(
        self,
        *,
        client_id: str,
        service_id: str,
        addition_id: str,
        montant: int,
        auteur_id: str,
    ) -> None:
        try:
            self._accorder_credit.executer(
                AccorderCreditCommand(
                    client_id=client_id,
                    service_id=service_id,
                    addition_id=addition_id,
                    montant=montant,
                    auteur_id=auteur_id,
                )
            )
        except ClientIntrouvable as erreur:
            # Traduite dans le vocabulaire de l'appelant : Service & Ventes n'a
            # pas à connaître les exceptions d'un contexte qu'il ignore.
            raise ClientInconnu(client_id) from erreur
