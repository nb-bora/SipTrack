"""Routes REST du contexte Catalogue."""

from django.urls import path

from .views import (
    CatalogueListView,
    ProduitCreateView,
    ProduitRetraitView,
    TarifUpdateView,
)

urlpatterns = [
    path("produits/", ProduitCreateView.as_view(), name="produits"),
    path("bars/<str:bar_id>/produits/", CatalogueListView.as_view(), name="catalogue-bar"),
    path("produits/<str:produit_id>/tarif/", TarifUpdateView.as_view(), name="tarif"),
    path("produits/<str:produit_id>/retrait/", ProduitRetraitView.as_view(), name="retrait"),
]
