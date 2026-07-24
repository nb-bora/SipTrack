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
