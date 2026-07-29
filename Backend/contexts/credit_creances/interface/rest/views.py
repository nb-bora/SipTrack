"""Vues REST du contexte Crédit & Créances.

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
from contexts.credit_creances.application.dto import (
    CreerClientCommand,
    EnregistrerRemboursementCommand,
)
from contexts.credit_creances.domain.exceptions import (
    CreditDejaSolde,
    CreditIntrouvable,
    RemboursementSuperieurAuReste,
)
from shared.application.controle_acces import CapaciteRequise
from shared.interface.rest.acces import bar_ou_404, exiger_capacite, exiger_lecture

from .serializers import (
    ClientOutputSerializer,
    CreditOutputSerializer,
    CreerClientInputSerializer,
    EncoursClientOutputSerializer,
    EnregistrerRemboursementInputSerializer,
)

_CREDIT_INTROUVABLE = "Crédit introuvable."

_ETIQUETTES = ["Crédit & Créances"]


def _erreur(description: str) -> OpenApiResponse:
    return OpenApiResponse(response=OpenApiTypes.OBJECT, description=description)


def _validation() -> OpenApiResponse:
    return OpenApiResponse(
        response=OpenApiTypes.OBJECT,
        description="Requête invalide — dictionnaire `champ → [messages d'erreur]`.",
    )


class ClientCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Enregistrer un client",
        description=(
            "Idempotent : un nom déjà connu dans ce bar renvoie le client existant "
            "plutôt qu'un doublon, pour qu'une même personne ne porte pas deux dettes "
            "séparées."
        ),
        request=CreerClientInputSerializer,
        responses={
            201: ClientOutputSerializer,
            400: _validation(),
        },
    )
    def post(self, request: Request) -> Response:
        entree = CreerClientInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        exiger_capacite(
            request,
            bar_id=entree.validated_data["bar_id"],
            capacite=CapaciteRequise.CREER_CLIENT,
            operation="creer un client",
        )
        dto = container.creer_client().executer(
            CreerClientCommand(
                bar_id=entree.validated_data["bar_id"],
                nom=entree.validated_data["nom"],
            )
        )
        return Response(ClientOutputSerializer(dto).data, status=status.HTTP_201_CREATED)


class RemboursementCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Encaisser un remboursement",
        description=(
            "Partiel ou total. Le crédit s'éteint de lui-même quand le cumul des "
            "remboursements atteint le montant dû : le solde est une conséquence, "
            "jamais une déclaration."
        ),
        request=EnregistrerRemboursementInputSerializer,
        responses={
            201: CreditOutputSerializer,
            400: _validation(),
            404: _erreur("Crédit introuvable."),
            409: _erreur("Crédit déjà soldé, ou remboursement supérieur au reste dû."),
        },
    )
    def post(self, request: Request, credit_id: str) -> Response:
        entree = EnregistrerRemboursementInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        commande = EnregistrerRemboursementCommand(
            credit_id=credit_id,
            montant=entree.validated_data["montant"],
            auteur_id=exiger_capacite(
                request,
                bar_id=bar_ou_404(
                    container.bar_du_credit(credit_id), introuvable="Crédit introuvable."
                ),
                capacite=CapaciteRequise.ENCAISSER_REMBOURSEMENT,
                operation="encaisser un remboursement",
            ),
        )

        try:
            dto = container.enregistrer_remboursement().executer(commande)
        except CreditIntrouvable:
            return Response({"detail": _CREDIT_INTROUVABLE}, status=status.HTTP_404_NOT_FOUND)
        except CreditDejaSolde as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)
        except RemboursementSuperieurAuReste as erreur:
            return Response(
                {"detail": str(erreur), "reste": erreur.reste},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(CreditOutputSerializer(dto).data, status=status.HTTP_201_CREATED)


class EncoursClientView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="L'encours d'un client",
        description="Ce qu'un client doit, avec le détail de chaque créance.",
        responses={
            200: EncoursClientOutputSerializer,
            404: _erreur("Client introuvable."),
        },
    )
    def get(self, request: Request, client_id: str) -> Response:
        exiger_lecture(
            request,
            bar_id=bar_ou_404(
                container.bar_du_client(client_id), introuvable="Crédit introuvable."
            ),
            operation="lire un encours",
        )
        encours = container.encours_du_client(client_id)
        if encours is None:
            return Response({"detail": "Client introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EncoursClientOutputSerializer(encours).data)


class EncoursListView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Tous les encours d'un bar",
        description=(
            "La vue de la gérante : qui doit quoi. Un client dont toutes les dettes "
            "sont éteintes n'y figure pas."
        ),
        responses={200: EncoursClientOutputSerializer(many=True)},
    )
    def get(self, request: Request, bar_id: str) -> Response:
        exiger_lecture(request, bar_id=bar_id, operation="lire les encours")
        encours = container.encours_du_bar(bar_id)
        return Response(EncoursClientOutputSerializer(encours, many=True).data)
