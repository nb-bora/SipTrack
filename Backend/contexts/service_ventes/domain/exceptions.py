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


class AdditionDejaCloturee(ServiceVentesError):
    """Une opération a été tentée sur une addition déjà réglée/abandonnée."""

    def __init__(self, addition_id: str) -> None:
        super().__init__(f"L'addition {addition_id} est déjà clôturée.")
        self.addition_id = addition_id
