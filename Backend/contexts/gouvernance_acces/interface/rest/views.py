"""Obtention d'un jeton d'accès."""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from config.container import container
from contexts.gouvernance_acces.application.dto import (
    AccorderCapaciteCommand,
    CreerBarCommand,
    CreerCompteCommand,
    RetirerCapaciteCommand,
)
from contexts.gouvernance_acces.domain.exceptions import (
    AutoriseNonAutorisé,
    BarDejaExistant,
    BarIntrouvable,
    CompteDejaExistant,
    CompteIntrouvable,
)
from shared.interface.rest.acces import exiger_lecture
from shared.interface.rest.attribution import auteur_id_de

from .serializers import (
    AccesPlateformeOutputSerializer,
    AccorderCapaciteInputSerializer,
    BarOutputSerializer,
    CompteOutputSerializer,
    CreerBarInputSerializer,
    CreerCompteInputSerializer,
    RetirerCapaciteInputSerializer,
)


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


# ============================================================================
# Gestion des bars et comptes (le socle Gouvernance)
# ============================================================================

_ETIQUETTES = ["Gouvernance & Accès"]


def _erreur(description: str) -> OpenApiResponse:
    return OpenApiResponse(response=OpenApiTypes.OBJECT, description=description)


def _validation() -> OpenApiResponse:
    return OpenApiResponse(
        response=OpenApiTypes.OBJECT,
        description="Requête invalide — dictionnaire `champ → [messages d'erreur]`.",
    )


class BarListCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Créer un bar",
        description="Seul le propriétaire authentifié peut créer un bar.",
        request=CreerBarInputSerializer,
        responses={
            201: BarOutputSerializer,
            400: _validation(),
            409: _erreur("Un bar avec ce nom existe déjà."),
        },
    )
    def post(self, request: Request) -> Response:
        entree = CreerBarInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            dto = container.gerer_bars().creer(
                CreerBarCommand(
                    nom=entree.validated_data["nom"],
                    proprietaire_id=auteur_id_de(request),
                )
            )
        except BarDejaExistant as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(BarOutputSerializer(dto).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=_ETIQUETTES,
        summary="Lister mes bars",
        description="Liste tous les bars que je possède.",
        responses={200: BarOutputSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        bars = container.gerer_bars().lister(auteur_id_de(request))
        return Response(BarOutputSerializer(bars, many=True).data)


class CompteCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Créer un compte utilisateur",
        description=(
            "Créer un compte pour un utilisateur dans un bar. Requiert la capacité CREER_COMPTE."
        ),
        request=CreerCompteInputSerializer,
        responses={
            201: CompteOutputSerializer,
            400: _validation(),
            404: _erreur("Bar introuvable."),
            409: _erreur("Un compte existe déjà pour cet utilisateur dans ce bar."),
        },
    )
    def post(self, request: Request) -> Response:
        entree = CreerCompteInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            dto = container.gerer_comptes().creer(
                CreerCompteCommand(
                    bar_id=entree.validated_data["bar_id"],
                    user_id=entree.validated_data["user_id"],
                    capacites_initiales=frozenset(
                        entree.validated_data.get("capacites_initiales", [])
                    ),
                    auteur_id=auteur_id_de(request),
                )
            )
        except BarIntrouvable:
            return Response({"detail": "Bar introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except CompteDejaExistant as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)
        except AutoriseNonAutorisé as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(CompteOutputSerializer(dto).data, status=status.HTTP_201_CREATED)


class CapaciteUpdateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Accorder une capacité",
        request=AccorderCapaciteInputSerializer,
        responses={
            200: CompteOutputSerializer,
            404: _erreur("Compte introuvable."),
            409: _erreur("Capacité déjà accordée, ou non autorisé."),
        },
    )
    def post(self, request: Request, compte_id: str) -> Response:
        entree = AccorderCapaciteInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            dto = container.gerer_comptes().accorder_capacite(
                AccorderCapaciteCommand(
                    compte_id=compte_id,
                    capacite=entree.validated_data["capacite"],
                    auteur_id=auteur_id_de(request),
                )
            )
        except CompteIntrouvable:
            return Response({"detail": "Compte introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except (AutoriseNonAutorisé, Exception) as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(CompteOutputSerializer(dto).data)

    @extend_schema(
        tags=_ETIQUETTES,
        summary="Retirer une capacité",
        request=RetirerCapaciteInputSerializer,
        responses={
            200: CompteOutputSerializer,
            404: _erreur("Compte introuvable."),
            409: _erreur("Capacité non accordée, ou non autorisé."),
        },
    )
    def delete(self, request: Request, compte_id: str) -> Response:
        entree = RetirerCapaciteInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            dto = container.gerer_comptes().retirer_capacite(
                RetirerCapaciteCommand(
                    compte_id=compte_id,
                    capacite=entree.validated_data["capacite"],
                    auteur_id=auteur_id_de(request),
                )
            )
        except CompteIntrouvable:
            return Response({"detail": "Compte introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except (AutoriseNonAutorisé, Exception) as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(CompteOutputSerializer(dto).data)


class AccesPlateformeListView(APIView):
    """Qui, hors du bar, a consulté ses données.

    C'est la contrepartie du privilège de lecture des comptes plateforme : sans
    cette vue, la trace existerait sans que personne ne puisse la lire, et le
    privilège reviendrait à regarder sans être vu.
    """

    @extend_schema(
        tags=_ETIQUETTES,
        summary="Consultations faites par la plateforme sur ce bar",
        description=(
            "Les consultations d'une personne travaillant dans le bar n'y figurent "
            "pas : seules celles exercées au titre du privilège plateforme."
        ),
        responses={
            200: AccesPlateformeOutputSerializer(many=True),
            403: OpenApiResponse(description="Aucun compte dans ce bar."),
        },
    )
    def get(self, request: Request, bar_id: str) -> Response:
        exiger_lecture(request, bar_id=bar_id, operation="lire les acces au bar")
        return Response(
            AccesPlateformeOutputSerializer(container.acces_du_bar(bar_id), many=True).data
        )
