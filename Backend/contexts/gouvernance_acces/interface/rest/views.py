"""Obtention d'un jeton d'accès."""

from __future__ import annotations

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import ScopedRateThrottle


class ObtenirJetonView(ObtainAuthToken):
    """Échange identifiants contre jeton.

    `ObtainAuthToken` neutralise le throttling par défaut (`throttle_classes =
    ()`). On le réactive explicitement : c'est la seule route ouverte du
    système, donc la seule exposée au bourrinage de mots de passe.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "obtention_jeton"
