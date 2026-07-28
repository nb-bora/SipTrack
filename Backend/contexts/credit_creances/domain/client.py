"""Agrégat racine : Client.

Un client auprès duquel le bar peut accorder du crédit. Agrégat minimal
(cf. ADR-0004) qui porte uniquement ce qui est strictement nécessaire :
l'identité du client dans le contexte du bar.
"""

from __future__ import annotations

from shared.domain.identifiers import new_id


class Client:
    def __init__(
        self,
        *,
        id: str,
        bar_id: str,
        nom: str,
    ) -> None:
        self.id = id
        self.bar_id = bar_id
        self.nom = nom

    @classmethod
    def creer(
        cls,
        *,
        bar_id: str,
        nom: str,
    ) -> Client:
        """Crée un nouveau client."""
        return cls(
            id=new_id(),
            bar_id=bar_id,
            nom=nom,
        )
