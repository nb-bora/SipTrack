"""Permissions transverses à tous les contextes."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class AccesDocumentation(BasePermission):
    """Ouvre la documentation en développement, la ferme partout ailleurs.

    En développement le navigateur ne porte aucun jeton : sans cette ouverture,
    Swagger ne pourrait pas charger son schéma et afficherait une page vide.
    Ailleurs, la carte complète de l'API n'a pas à être publique.

    La décision est prise **à la requête**, pas à l'import : figée au chargement
    des URLs, elle serait impossible à vérifier en test — Django force
    `DEBUG = False` pendant les tests.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        if settings.DEBUG:
            return True
        return bool(request.user and request.user.is_authenticated)
