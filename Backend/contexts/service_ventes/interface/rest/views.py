"""Vues REST du contexte Service & Ventes.

Les vues ne contiennent aucune règle métier : elles valident l'entrée (DTO),
délèguent au cas d'usage fourni par le composition root, et sérialisent la sortie.

L'auteur d'un fait n'est jamais lu dans le corps de la requête : il est tiré de
la requête authentifiée (cf. `shared.interface.rest.attribution`).
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.container import container
from contexts.service_ventes.application.dto import (
    CloturerServiceCommand,
    EnregistrerPaiementCommand,
    EnregistrerVenteCommand,
    OuvrirAdditionCommand,
    OuvrirServiceCommand,
    ReglementAdditionCommand,
    VerserRecetteCommand,
)
from contexts.service_ventes.domain.exceptions import (
    AdditionDejaCloturee,
    AdditionIntrouvable,
    AdditionNonSoldee,
    AdditionsEncoreOuvertes,
    PaiementSuperieurAuReste,
    RecetteDejaVersee,
    ServiceDejaCloture,
    ServiceIntrouvable,
    ServiceNonOuvert,
)
from shared.interface.rest.attribution import auteur_id_de

from .serializers import (
    AdditionDetailOutputSerializer,
    AdditionOutputSerializer,
    EnregistrerPaiementInputSerializer,
    EnregistrerVenteInputSerializer,
    ErreurSerializer,
    OuvrirAdditionInputSerializer,
    OuvrirServiceInputSerializer,
    PaiementOutputSerializer,
    ServiceOutputSerializer,
    SousCaisseOutputSerializer,
    VenteOutputSerializer,
    VersementOutputSerializer,
    VerserRecetteInputSerializer,
)

_SERVICE_INTROUVABLE = "Service introuvable."
_ADDITION_INTROUVABLE = "Addition introuvable."
_ADDITION_CLOTUREE = "L'addition est déjà clôturée."

_ETIQUETTES = ["Service & Ventes"]


def _erreur(description: str) -> OpenApiResponse:
    return OpenApiResponse(response=ErreurSerializer, description=description)


def _validation() -> OpenApiResponse:
    """Réponse 400 de DRF, à documenter explicitement.

    Dès qu'on surcharge `responses`, drf-spectacular cesse d'ajouter le 400 par
    défaut : sans cette entrée, le contrat tairait une réponse pourtant possible
    à chaque endpoint qui valide une entrée.
    """
    return OpenApiResponse(
        response=OpenApiTypes.OBJECT,
        description="Requête invalide — dictionnaire `champ → [messages d'erreur]`.",
    )


class ServiceListCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Ouvrir un service",
        description=(
            "Ouvre une période de responsabilité. L'auteur est déduit du compte "
            "authentifié ; `capacite` est déclarée pour cet acte précis."
        ),
        request=OuvrirServiceInputSerializer,
        responses={
            201: ServiceOutputSerializer,
            400: _validation(),
        },
    )
    def post(self, request: Request) -> Response:
        entree = OuvrirServiceInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = OuvrirServiceCommand(
            auteur_id=auteur_id_de(request),
            **entree.validated_data,
        )

        dto = container.ouvrir_service().executer(commande)

        return Response(
            ServiceOutputSerializer(dto).data,
            status=status.HTTP_201_CREATED,
        )


class ServiceDetailView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Lire un service",
        responses={
            200: ServiceOutputSerializer,
            404: _erreur("Service introuvable."),
        },
    )
    def get(self, request: Request, service_id: str) -> Response:
        dto = container.service_par_id(service_id)
        if dto is None:
            return Response(
                {"detail": _SERVICE_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ServiceOutputSerializer(dto).data)


class VenteCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Enregistrer une vente",
        description=(
            "Enregistre une consommation sur un service ouvert. `addition_id` est "
            "facultatif : une vente au comptoir n'est rattachée à aucune table."
        ),
        request=EnregistrerVenteInputSerializer,
        responses={
            201: VenteOutputSerializer,
            400: _validation(),
            404: _erreur("Service introuvable, ou addition inexistante / d'un autre service."),
            409: _erreur("Service non ouvert, ou addition déjà clôturée."),
        },
    )
    def post(self, request: Request, service_id: str) -> Response:
        entree = EnregistrerVenteInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = EnregistrerVenteCommand(
            service_id=service_id,
            auteur_id=auteur_id_de(request),
            **entree.validated_data,
        )

        try:
            dto = container.enregistrer_vente().executer(commande)
        except ServiceIntrouvable:
            return Response(
                {"detail": _SERVICE_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AdditionIntrouvable:
            return Response(
                {"detail": _ADDITION_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceNonOuvert:
            return Response(
                {"detail": "Le service n'est pas ouvert."},
                status=status.HTTP_409_CONFLICT,
            )
        except AdditionDejaCloturee:
            return Response(
                {"detail": _ADDITION_CLOTUREE},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            VenteOutputSerializer(dto).data,
            status=status.HTTP_201_CREATED,
        )


class CloturerServiceView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Clôturer un service",
        description=(
            "Aucun corps de requête : l'auteur vient du compte authentifié. "
            "La clôture est refusée tant qu'une addition reste ouverte."
        ),
        request=None,
        responses={
            200: ServiceOutputSerializer,
            404: _erreur("Service introuvable."),
            409: _erreur("Service déjà clôturé, ou additions encore ouvertes."),
        },
    )
    def post(self, request: Request, service_id: str) -> Response:
        commande = CloturerServiceCommand(
            service_id=service_id,
            auteur_id=auteur_id_de(request),
        )

        try:
            dto = container.cloturer_service().executer(commande)
        except ServiceIntrouvable:
            return Response(
                {"detail": _SERVICE_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceDejaCloture:
            return Response(
                {"detail": "Le service est déjà clôturé."},
                status=status.HTTP_409_CONFLICT,
            )
        except AdditionsEncoreOuvertes as erreur:
            # On dit combien : une gérante doit savoir ce qui lui reste à faire.
            return Response(
                {
                    "detail": (
                        f"Impossible de clôturer : {erreur.nombre} addition(s) encore ouverte(s)."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            ServiceOutputSerializer(dto).data,
            status=status.HTTP_200_OK,
        )


class AdditionListCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Ouvrir une addition",
        request=OuvrirAdditionInputSerializer,
        responses={
            201: AdditionOutputSerializer,
            400: _validation(),
            404: _erreur("Service introuvable."),
            409: _erreur("Service non ouvert."),
        },
    )
    def post(self, request: Request, service_id: str) -> Response:
        entree = OuvrirAdditionInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = OuvrirAdditionCommand(
            service_id=service_id,
            auteur_id=auteur_id_de(request),
            **entree.validated_data,
        )

        try:
            dto = container.ouvrir_addition().executer(commande)
        except ServiceIntrouvable:
            return Response(
                {"detail": _SERVICE_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceNonOuvert:
            return Response(
                {"detail": "Le service n'est pas ouvert."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            AdditionOutputSerializer(dto).data,
            status=status.HTTP_201_CREATED,
        )


class AdditionDetailView(APIView):
    """Lecture d'une addition : ses lignes et son total, calculé à la volée."""

    @extend_schema(
        tags=_ETIQUETTES,
        summary="Lire une addition (lignes et total)",
        description="Le total est recalculé à chaque lecture depuis les ventes rattachées.",
        responses={
            200: AdditionDetailOutputSerializer,
            404: _erreur("Addition inexistante, ou rattachée à un autre service."),
        },
    )
    def get(self, request: Request, service_id: str, addition_id: str) -> Response:
        dto = container.addition_detail(service_id=service_id, addition_id=addition_id)
        if dto is None:
            return Response(
                {"detail": _ADDITION_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(AdditionDetailOutputSerializer(dto).data)


class PaiementCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Encaisser un paiement sur une addition",
        description=(
            "Encaisse tout ou partie de ce que la table doit. Quand le cumul des "
            "paiements couvre le total consommé, l'addition passe d'elle-même à "
            "`reglee` — le règlement est une conséquence, pas une déclaration."
        ),
        request=EnregistrerPaiementInputSerializer,
        responses={
            201: PaiementOutputSerializer,
            400: _validation(),
            404: _erreur("Addition inexistante, ou rattachée à un autre service."),
            409: _erreur("Addition déjà clôturée, ou paiement supérieur au reste dû."),
        },
    )
    def post(self, request: Request, service_id: str, addition_id: str) -> Response:
        entree = EnregistrerPaiementInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = EnregistrerPaiementCommand(
            service_id=service_id,
            addition_id=addition_id,
            auteur_id=auteur_id_de(request),
            **entree.validated_data,
        )

        try:
            dto = container.enregistrer_paiement().executer(commande)
        except AdditionIntrouvable:
            return Response(
                {"detail": _ADDITION_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AdditionDejaCloturee:
            return Response(
                {"detail": _ADDITION_CLOTUREE},
                status=status.HTTP_409_CONFLICT,
            )
        except PaiementSuperieurAuReste as erreur:
            return Response(
                {"detail": f"Paiement supérieur au reste dû ({erreur.reste})."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            PaiementOutputSerializer(dto).data,
            status=status.HTTP_201_CREATED,
        )


class ReglementAdditionView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Régler une addition",
        description="Aucun corps de requête : l'auteur vient du compte authentifié.",
        request=None,
        responses={
            200: AdditionOutputSerializer,
            404: _erreur("Addition inexistante, ou rattachée à un autre service."),
            409: _erreur("Addition déjà réglée, abandonnée, ou non soldée."),
        },
    )
    def post(self, request: Request, service_id: str, addition_id: str) -> Response:
        commande = ReglementAdditionCommand(
            service_id=service_id,
            addition_id=addition_id,
            auteur_id=auteur_id_de(request),
        )

        try:
            dto = container.regler_addition().executer(commande)
        except AdditionIntrouvable:
            return Response(
                {"detail": _ADDITION_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AdditionDejaCloturee:
            return Response(
                {"detail": _ADDITION_CLOTUREE},
                status=status.HTTP_409_CONFLICT,
            )
        except AdditionNonSoldee as erreur:
            return Response(
                {"detail": f"L'addition n'est pas soldée : reste {erreur.reste} à encaisser."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            AdditionOutputSerializer(dto).data,
            status=status.HTTP_200_OK,
        )


class VersementCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Verser sa recette",
        description=(
            "La serveuse remet sa recette en espèces. Elle verse **pour elle-même** : "
            "l'identité vient du jeton. L'attendu est la somme de ses encaissements en "
            "espèces — le mobile money n'est pas remis de la main à la main. Tout écart, "
            "même d'un franc, part au journal comme Fait."
        ),
        request=VerserRecetteInputSerializer,
        responses={
            201: VersementOutputSerializer,
            400: _validation(),
            404: _erreur("Service introuvable."),
            409: _erreur("Service non ouvert, ou recette déjà versée."),
        },
    )
    def post(self, request: Request, service_id: str) -> Response:
        entree = VerserRecetteInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = VerserRecetteCommand(
            service_id=service_id,
            serveuse_id=auteur_id_de(request),
            **entree.validated_data,
        )

        try:
            dto = container.verser_recette().executer(commande)
        except ServiceIntrouvable:
            return Response(
                {"detail": _SERVICE_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceNonOuvert:
            return Response(
                {"detail": "Le service n'est pas ouvert."},
                status=status.HTTP_409_CONFLICT,
            )
        except RecetteDejaVersee:
            return Response(
                {"detail": "Votre recette a déjà été versée sur ce service."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            VersementOutputSerializer(dto).data,
            status=status.HTTP_201_CREATED,
        )


class SousCaisseListView(APIView):
    """La réconciliation quotidienne, vue par la gérante."""

    @extend_schema(
        tags=_ETIQUETTES,
        summary="Lire les sous-caisses d'un service",
        description=(
            "Par personne ayant encaissé : ce qu'elle doit rapporter en espèces, ce "
            "qu'elle a remis, et l'écart. `verse` et `ecart` sont nuls tant qu'elle "
            "n'a pas versé."
        ),
        responses={200: SousCaisseOutputSerializer(many=True)},
    )
    def get(self, request: Request, service_id: str) -> Response:
        dtos = container.sous_caisses_du_service(service_id)
        return Response(SousCaisseOutputSerializer(dtos, many=True).data)
