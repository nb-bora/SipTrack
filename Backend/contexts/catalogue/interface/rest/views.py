"""Vues REST du contexte Catalogue.

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
from contexts.catalogue.application.dto import (
    ChangerLeTarifCommand,
    InscrireProduitCommand,
    RetirerProduitCommand,
)
from contexts.catalogue.domain.exceptions import (
    ProduitDejaInscrit,
    ProduitIntrouvable,
    TarifInchange,
)
from shared.application.controle_acces import CapaciteRequise
from shared.interface.rest.acces import bar_ou_404, exiger_capacite, exiger_lecture

from .serializers import (
    ChangerLeTarifInputSerializer,
    InscrireProduitInputSerializer,
    ProduitOutputSerializer,
)

_PRODUIT_INTROUVABLE = "Produit introuvable."

_ETIQUETTES = ["Catalogue"]


def _erreur(description: str) -> OpenApiResponse:
    return OpenApiResponse(response=OpenApiTypes.OBJECT, description=description)


def _validation() -> OpenApiResponse:
    return OpenApiResponse(
        response=OpenApiTypes.OBJECT,
        description="Requête invalide — dictionnaire `champ → [messages d'erreur]`.",
    )


class ProduitCreateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Inscrire un produit au catalogue",
        description=(
            "Le prix inscrit ici fait autorité : c'est lui qui sera appliqué aux "
            "ventes, jamais un prix envoyé avec la vente."
        ),
        request=InscrireProduitInputSerializer,
        responses={
            201: ProduitOutputSerializer,
            400: _validation(),
            409: _erreur("Ce nom figure déjà au catalogue de ce bar."),
        },
    )
    def post(self, request: Request) -> Response:
        entree = InscrireProduitInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        commande = InscrireProduitCommand(
            bar_id=entree.validated_data["bar_id"],
            nom=entree.validated_data["nom"],
            prix=entree.validated_data["prix"],
            auteur_id=exiger_capacite(
                request,
                bar_id=entree.validated_data["bar_id"],
                capacite=CapaciteRequise.INSCRIRE_PRODUIT,
                operation="inscrire un produit",
            ),
        )
        try:
            dto = container.gerer_le_catalogue().inscrire(commande)
        except ProduitDejaInscrit as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(ProduitOutputSerializer(dto).data, status=status.HTTP_201_CREATED)


class CatalogueListView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Le catalogue d'un bar",
        description="Les produits retirés y figurent, marqués `en_vente: false`.",
        responses={200: ProduitOutputSerializer(many=True)},
    )
    def get(self, request: Request, bar_id: str) -> Response:
        exiger_lecture(request, bar_id=bar_id, operation="lire le catalogue")
        produits = container.catalogue_du_bar(bar_id)
        return Response(ProduitOutputSerializer(produits, many=True).data)


class TarifUpdateView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Changer le tarif d'un produit",
        description=(
            "Le changement est un Fait journalisé, avec l'ancien et le nouveau prix : "
            "sans cette trace, une recette qui baisse serait indiscernable d'un vol.\n\n"
            "Les ventes déjà saisies gardent leur prix — elles l'ont copié au moment "
            "de la saisie."
        ),
        request=ChangerLeTarifInputSerializer,
        responses={
            200: ProduitOutputSerializer,
            400: _validation(),
            404: _erreur("Produit introuvable."),
            409: _erreur("Le prix proposé est déjà celui en vigueur."),
        },
    )
    def post(self, request: Request, produit_id: str) -> Response:
        entree = ChangerLeTarifInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        commande = ChangerLeTarifCommand(
            produit_id=produit_id,
            nouveau_prix=entree.validated_data["prix"],
            auteur_id=exiger_capacite(
                request,
                bar_id=bar_ou_404(
                    container.bar_du_produit_catalogue(produit_id),
                    introuvable="Produit introuvable.",
                ),
                capacite=CapaciteRequise.TARIFER,
                operation="changer un tarif",
            ),
        )
        try:
            dto = container.gerer_le_catalogue().changer_le_tarif(commande)
        except ProduitIntrouvable:
            return Response({"detail": _PRODUIT_INTROUVABLE}, status=status.HTTP_404_NOT_FOUND)
        except TarifInchange as erreur:
            return Response({"detail": str(erreur)}, status=status.HTTP_409_CONFLICT)

        return Response(ProduitOutputSerializer(dto).data)


class ProduitRetraitView(APIView):
    @extend_schema(
        tags=_ETIQUETTES,
        summary="Retirer un produit de la vente",
        description=(
            "Le produit n'est jamais supprimé : les ventes passées le référencent, "
            "et les effacer rendrait illisible l'historique qu'on protège."
        ),
        request=None,
        responses={
            200: ProduitOutputSerializer,
            404: _erreur("Produit introuvable."),
        },
    )
    def post(self, request: Request, produit_id: str) -> Response:
        commande = RetirerProduitCommand(
            produit_id=produit_id,
            auteur_id=exiger_capacite(
                request,
                bar_id=bar_ou_404(
                    container.bar_du_produit_catalogue(produit_id),
                    introuvable="Produit introuvable.",
                ),
                capacite=CapaciteRequise.RETIRER_PRODUIT,
                operation="retirer un produit",
            ),
        )
        try:
            dto = container.gerer_le_catalogue().retirer(commande)
        except ProduitIntrouvable:
            return Response({"detail": _PRODUIT_INTROUVABLE}, status=status.HTTP_404_NOT_FOUND)

        return Response(ProduitOutputSerializer(dto).data)
