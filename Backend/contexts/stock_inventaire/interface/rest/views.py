"""Views REST pour Stock & Inventaire."""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.container import container
from contexts.stock_inventaire.application.dto import (
    AjouterStockCommand,
    CorrigerInventaireCommand,
    CreerProduitCommand,
    VendreCommand,
)
from contexts.stock_inventaire.domain.exceptions import (
    ProduitDejaExistant,
    ProduitIntrouvable,
    QuantiteInsuffisante,
    QuantiteNegative,
)
from shared.application.controle_acces import CapaciteRequise
from shared.interface.rest.acces import bar_ou_404, exiger_capacite, exiger_lecture

from .serializers import (
    AjouterStockInputSerializer,
    CorrigerInventaireInputSerializer,
    CreerProduitInputSerializer,
    InventaireProduitOutputSerializer,
    VendreInputSerializer,
)

_ETIQUETTES = ["Stock & Inventaire"]


def _erreur(description: str) -> OpenApiResponse:
    return OpenApiResponse(response=OpenApiTypes.OBJECT, description=description)


def _validation() -> OpenApiResponse:
    return OpenApiResponse(
        response=OpenApiTypes.OBJECT,
        description="Requête invalide — dictionnaire `champ → [messages d'erreur]`.",
    )


class ProduitListCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Créer un produit",
        request=CreerProduitInputSerializer,
        responses={
            201: InventaireProduitOutputSerializer,
            400: _validation(),
            409: _erreur("Un produit avec ce nom existe déjà dans le bar."),
        },
    )
    def post(self, request: Request) -> Response:
        entree = CreerProduitInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        exiger_capacite(
            request,
            bar_id=entree.validated_data["bar_id"],
            capacite=CapaciteRequise.INSCRIRE_PRODUIT,
            operation="inscrire un produit au stock",
        )
        try:
            dto = container.gerer_stock().creer_produit(
                CreerProduitCommand(
                    bar_id=entree.validated_data["bar_id"],
                    nom=entree.validated_data["nom"],
                    quantite_initiale=entree.validated_data["quantite_initiale"],
                )
            )
        except ProduitDejaExistant as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(InventaireProduitOutputSerializer(dto).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=_ETIQUETTES,
        summary="Lister les produits",
        responses={200: InventaireProduitOutputSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        bar_id = request.query_params.get("bar_id")
        if not bar_id:
            return Response(
                {"detail": "Paramètre bar_id requis"}, status=status.HTTP_400_BAD_REQUEST
            )
        exiger_lecture(request, bar_id=bar_id, operation="lire le stock")

        produits = container.gerer_stock().lister_produits(bar_id)
        return Response(InventaireProduitOutputSerializer(produits, many=True).data)


class StockAjouterView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Ajouter du stock",
        request=AjouterStockInputSerializer,
        responses={
            200: InventaireProduitOutputSerializer,
            404: _erreur("Produit introuvable."),
        },
    )
    def post(self, request: Request, produit_id: str) -> Response:
        entree = AjouterStockInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            dto = container.gerer_stock().ajouter_stock(
                AjouterStockCommand(
                    produit_id=produit_id,
                    quantite=entree.validated_data["quantite"],
                    auteur_id=exiger_capacite(
                        request,
                        bar_id=bar_ou_404(
                            container.bar_du_produit_stock(produit_id),
                            introuvable="Produit introuvable.",
                        ),
                        capacite=CapaciteRequise.ENREGISTRER_VENTE,
                        operation="mouvementer le stock",
                    ),
                )
            )
        except ProduitIntrouvable:
            return Response({"detail": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)

        return Response(InventaireProduitOutputSerializer(dto).data)


class VendreView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Enregistrer une vente",
        request=VendreInputSerializer,
        responses={
            200: InventaireProduitOutputSerializer,
            404: _erreur("Produit introuvable."),
            409: _erreur("Quantité insuffisante en stock."),
        },
    )
    def post(self, request: Request, produit_id: str) -> Response:
        entree = VendreInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            dto = container.gerer_stock().vendre(
                VendreCommand(
                    produit_id=produit_id,
                    quantite=entree.validated_data["quantite"],
                    auteur_id=exiger_capacite(
                        request,
                        bar_id=bar_ou_404(
                            container.bar_du_produit_stock(produit_id),
                            introuvable="Produit introuvable.",
                        ),
                        capacite=CapaciteRequise.ENREGISTRER_VENTE,
                        operation="mouvementer le stock",
                    ),
                )
            )
        except ProduitIntrouvable:
            return Response({"detail": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except QuantiteInsuffisante as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(InventaireProduitOutputSerializer(dto).data)


class CorrigerInventaireView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Corriger l'inventaire",
        request=CorrigerInventaireInputSerializer,
        responses={
            200: InventaireProduitOutputSerializer,
            404: _erreur("Produit introuvable."),
            400: _erreur("Quantité invalide."),
        },
    )
    def put(self, request: Request, produit_id: str) -> Response:
        entree = CorrigerInventaireInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            dto = container.gerer_stock().corriger_inventaire(
                CorrigerInventaireCommand(
                    produit_id=produit_id,
                    quantite_nouvelle=entree.validated_data["quantite_nouvelle"],
                    raison=entree.validated_data["raison"],
                    auteur_id=exiger_capacite(
                        request,
                        bar_id=bar_ou_404(
                            container.bar_du_produit_stock(produit_id),
                            introuvable="Produit introuvable.",
                        ),
                        capacite=CapaciteRequise.ENREGISTRER_VENTE,
                        operation="mouvementer le stock",
                    ),
                )
            )
        except ProduitIntrouvable:
            return Response({"detail": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except QuantiteNegative as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InventaireProduitOutputSerializer(dto).data)
