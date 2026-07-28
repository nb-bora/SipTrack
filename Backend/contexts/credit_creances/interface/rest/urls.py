"""Routes REST du contexte Crédit & Créances."""

from django.urls import path

from .views import (
    ClientCreateView,
    EncoursClientView,
    EncoursListView,
    RemboursementCreateView,
)

urlpatterns = [
    path("clients/", ClientCreateView.as_view(), name="clients"),
    path("clients/<str:client_id>/encours/", EncoursClientView.as_view(), name="encours-client"),
    path("bars/<str:bar_id>/encours/", EncoursListView.as_view(), name="encours-bar"),
    path(
        "credits/<str:credit_id>/remboursements/",
        RemboursementCreateView.as_view(),
        name="remboursements",
    ),
]
