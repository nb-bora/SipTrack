"""Permissions transverses à tous les contextes."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class AccesDocumentation(BasePermission):
    """La documentation API est toujours publique.

    La documentation Swagger/ReDoc est une ressource de découverte, pas sensible.
    Elle doit être accessible à tous, même en production, pour que les clients
    puissent explorer l'API sans avoir besoin de créer un compte.

    L'authentification protège les endpoints métier (/api/...), pas la doc.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        return True
