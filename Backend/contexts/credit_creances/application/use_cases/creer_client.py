"""Cas d'usage : enregistrer un client.

Un client existe pour qu'une dette puisse porter un nom. Rien de plus n'est
demandé : exiger un téléphone ou une pièce d'identité ferait renoncer la
serveuse au bon moment — et un crédit non saisi est pire qu'un crédit mal
renseigné.
"""

from __future__ import annotations

from contexts.credit_creances.application.dto import ClientDTO, CreerClientCommand
from contexts.credit_creances.domain.client import Client
from contexts.credit_creances.domain.repositories import ClientRepository
from shared.application.unit_of_work import UnitOfWork


class CreerClientHandler:
    def __init__(self, *, uow: UnitOfWork, clients: ClientRepository) -> None:
        self._uow = uow
        self._clients = clients

    def executer(self, commande: CreerClientCommand) -> ClientDTO:
        """Crée le client, ou renvoie celui qui porte déjà ce nom dans ce bar.

        Idempotent volontairement : en plein service, la serveuse ressaisit un
        nom sans savoir s'il existe déjà. Refuser créerait un doublon de dettes
        pour une même personne, ce qui est exactement ce qu'on veut éviter.
        """
        existant = self._clients.par_bar_et_nom(bar_id=commande.bar_id, nom=commande.nom)
        if existant is not None:
            return ClientDTO.depuis(existant)

        client = Client.creer(bar_id=commande.bar_id, nom=commande.nom)
        with self._uow:
            self._clients.ajouter(client)
            self._uow.commit()
        return ClientDTO.depuis(client)
