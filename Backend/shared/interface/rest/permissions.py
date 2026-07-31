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


class MotDePasseAJour(BasePermission):
    """Refuse l'accès si l'utilisateur doit changer son mot de passe.

    Les employés créés via l'endpoint /api/comptes/employe/ sont marqués
    comme devant changer leur mot de passe initial. Cette permission bloque
    l'accès à tous les endpoints sauf ceux exemptés (déconnexion, changement
    de mot de passe, etc.).
    """

    EXEMPTED_VIEWS = {"DeconnexionView", "ChangerMotDePasseView", "MoiView"}

    def has_permission(self, request: Request, view: Any) -> bool:
        from config.container import container

        # Exempter les vues listées
        if view.__class__.__name__ in self.EXEMPTED_VIEWS:
            return True

        if not request.user or not request.user.is_authenticated:
            return True

        user_id = str(request.user.pk)
        return not container.doit_changer_mot_de_passe(user_id)
