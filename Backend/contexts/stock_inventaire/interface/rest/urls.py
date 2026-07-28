"""URLs pour l'API REST de Stock & Inventaire."""

from django.urls import path

from .views import (
    CorrigerInventaireView,
    ProduitListCreateView,
    StockAjouterView,
    VendreView,
)

urlpatterns = [
    path("inventaire/produits/", ProduitListCreateView.as_view(), name="produit-list-create"),
    path(
        "inventaire/produits/<str:produit_id>/stock/",
        StockAjouterView.as_view(),
        name="stock-ajouter",
    ),
    path("inventaire/produits/<str:produit_id>/vendre/", VendreView.as_view(), name="vendre"),
    path(
        "inventaire/produits/<str:produit_id>/inventaire/",
        CorrigerInventaireView.as_view(),
        name="inventaire-corriger",
    ),
]
