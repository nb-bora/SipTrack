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


class AdditionDejaCloturee(ServiceVentesError):
    """Une opération a été tentée sur une addition déjà réglée/abandonnée."""

    def __init__(self, addition_id: str) -> None:
        super().__init__(f"L'addition {addition_id} est déjà clôturée.")
        self.addition_id = addition_id
