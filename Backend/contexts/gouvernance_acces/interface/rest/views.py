"""Obtention d'un jeton d'accès."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import ScopedRateThrottle


@extend_schema(
    tags=["Gouvernance & Accès"],
    summary="Obtenir un jeton",
    description=(
        "Seule route ouverte du système. Le jeton obtenu se présente ensuite sur "
        "chaque appel : `Authorization: Token <jeton>`. Il n'expire pas — l'app "
        "mobile est offline-first — et se révoque en supprimant sa ligne."
    ),
    request=AuthTokenSerializer,
    responses={
        200: inline_serializer(
            name="Jeton",
            fields={"token": serializers.CharField()},
        ),
        400: inline_serializer(
            name="IdentifiantsInvalides",
            fields={"non_field_errors": serializers.ListField(child=serializers.CharField())},
        ),
    },
)
class ObtenirJetonView(ObtainAuthToken):
    """Échange identifiants contre jeton.

    `ObtainAuthToken` neutralise le throttling par défaut (`throttle_classes =
    ()`). On le réactive explicitement : c'est la seule route ouverte du
    système, donc la seule exposée au bourrinage de mots de passe.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "obtention_jeton"
