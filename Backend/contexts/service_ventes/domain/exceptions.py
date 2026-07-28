"""Erreurs métier du contexte Service & Ventes."""

from __future__ import annotations


class ServiceVentesError(Exception):
    """Erreur de base du contexte."""


class ServiceDejaCloture(ServiceVentesError):
    """Une opération a été tentée sur un service déjà clôturé/scellé."""


class ServiceIntrouvable(ServiceVentesError):
    """Aucun service ne correspond à l'identifiant fourni."""

    def __init__(self, service_id: str) -> None:
        super().__init__(f"Service introuvable : {service_id}.")
        self.service_id = service_id


class ServiceNonOuvert(ServiceVentesError):
    """Une vente a été tentée sur un service qui n'est pas ouvert."""

    def __init__(self, service_id: str) -> None:
        super().__init__(f"Le service {service_id} n'est pas ouvert.")
        self.service_id = service_id


class AdditionIntrouvable(ServiceVentesError):
    """Aucune addition ne correspond à l'identifiant fourni."""

    def __init__(self, addition_id: str) -> None:
        super().__init__(f"Addition introuvable : {addition_id}.")
        self.addition_id = addition_id


class AdditionsEncoreOuvertes(ServiceVentesError):
    """Clôture refusée : des tables n'ont pas réglé.

    Clôturer malgré tout ferait disparaître du décompte de la journée des
    consommations servies mais non réglées (invariant 9 du modèle métier).
    """

    def __init__(self, service_id: str, nombre: int) -> None:
        super().__init__(f"Le service {service_id} a encore {nombre} addition(s) ouverte(s).")
        self.service_id = service_id
        self.nombre = nombre


class PaiementSuperieurAuReste(ServiceVentesError):
    """Encaissement refusé : il dépasse ce que la table doit encore.

    Rendre la monnaie est un autre Fait, pas un paiement négatif déguisé.
    """

    def __init__(self, addition_id: str, reste: int) -> None:
        super().__init__(f"L'addition {addition_id} ne doit plus que {reste}.")
        self.addition_id = addition_id
        self.reste = reste


class AdditionNonSoldee(ServiceVentesError):
    """Clôture d'addition refusée : il reste quelque chose à encaisser."""

    def __init__(self, addition_id: str, reste: int) -> None:
        super().__init__(f"L'addition {addition_id} n'est pas soldée : reste {reste}.")
        self.addition_id = addition_id
        self.reste = reste


class RecetteDejaVersee(ServiceVentesError):
    """Une serveuse ne verse qu'une fois par service.

    Un second versement masquerait le premier : une correction s'ecrit par
    contre-passation, pas en repassant par-dessus.
    """

    def __init__(self, service_id: str, serveuse_id: str) -> None:
        super().__init__(
            f"La recette de {serveuse_id} a deja ete versee sur le service {service_id}."
        )
        self.service_id = service_id
        self.serveuse_id = serveuse_id


class AdditionDejaCloturee(ServiceVentesError):
    """Une opération a été tentée sur une addition déjà réglée/abandonnée."""

    def __init__(self, addition_id: str) -> None:
        super().__init__(f"L'addition {addition_id} est déjà clôturée.")
        self.addition_id = addition_id


class ClientRequisPourUnCredit(ServiceVentesError):
    """Encaissement en crédit refusé : personne n'est désigné comme débiteur.

    Un crédit sans client, c'est de l'argent qui disparaît sans que quiconque
    doive rien. C'est précisément le trou que le crédit est censé fermer.
    """

    def __init__(self, addition_id: str) -> None:
        super().__init__(f"Un crédit sur l'addition {addition_id} exige un client.")
        self.addition_id = addition_id


class ClientInconnu(ServiceVentesError):
    """Le client désigné comme débiteur n'existe pas."""

    def __init__(self, client_id: str) -> None:
        super().__init__(f"Client introuvable : {client_id}.")
        self.client_id = client_id
