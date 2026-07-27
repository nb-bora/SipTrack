"""Vues REST du contexte Service & Ventes.

Les vues ne contiennent aucune règle métier : elles valident l'entrée (DTO),
délèguent au cas d'usage fourni par le composition root, et sérialisent la sortie.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.container import container
from contexts.service_ventes.application.dto import (
    CloturerServiceCommand,
    EnregistrerVenteCommand,
    OuvrirServiceCommand,
)
from contexts.service_ventes.domain.exceptions import (
    ServiceDejaCloture,
    ServiceIntrouvable,
    ServiceNonOuvert,
)

from .serializers import (
    CloturerServiceInputSerializer,
    EnregistrerVenteInputSerializer,
    OuvrirServiceInputSerializer,
    ServiceOutputSerializer,
    VenteOutputSerializer,
)

_SERVICE_INTROUVABLE = "Service introuvable."


class ServiceListCreateView(APIView):
    def post(self, request: Request) -> Response:
        entree = OuvrirServiceInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = OuvrirServiceCommand(**entree.validated_data)

        dto = container.ouvrir_service().executer(commande)

        return Response(
            ServiceOutputSerializer(dto).data,
            status=status.HTTP_201_CREATED,
        )


class ServiceDetailView(APIView):
    def get(self, request: Request, service_id: str) -> Response:
        dto = container.service_par_id(service_id)
        if dto is None:
            return Response(
                {"detail": _SERVICE_INTROUVABLE},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ServiceOutputSerializer(dto).data)


class VenteCreateView(APIView):
    def post(self, request: Request, service_id: str) -> Response:
        entree = EnregistrerVenteInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = EnregistrerVenteCommand(service_id=service_id, **entree.validated_data)

        try:
            dto = container.enregistrer_vente().executer(commande)
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
            VenteOutputSerializer(dto).data,
            status=status.HTTP_201_CREATED,
        )


class CloturerServiceView(APIView):
    def post(self, request: Request, service_id: str) -> Response:
        entree = CloturerServiceInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        commande = CloturerServiceCommand(service_id=service_id, **entree.validated_data)

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

        return Response(
            ServiceOutputSerializer(dto).data,
            status=status.HTTP_200_OK,
        )
