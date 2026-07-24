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
from contexts.service_ventes.application.dto import OuvrirServiceCommand

from .serializers import OuvrirServiceInputSerializer, ServiceOutputSerializer


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
                {"detail": "Service introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ServiceOutputSerializer(dto).data)
