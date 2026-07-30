"""Routes REST du contexte Gouvernance & Accès."""

from __future__ import annotations

from django.urls import path

from .views import (
    AccesPlateformeListView,
    BarListCreateView,
    CapaciteUpdateView,
    CompteCreateView,
    DeconnexionView,
    InscrireView,
    ObtenirJetonView,
)

urlpatterns = [
    path("inscription/", InscrireView.as_view(), name="inscription"),
    path("auth/jeton/", ObtenirJetonView.as_view(), name="obtenir-jeton"),
    path("auth/deconnexion/", DeconnexionView.as_view(), name="deconnexion"),
    path("bars/", BarListCreateView.as_view(), name="bars"),
    path("bars/<str:bar_id>/acces/", AccesPlateformeListView.as_view(), name="acces-bar"),
    path("comptes/", CompteCreateView.as_view(), name="comptes"),
    path("comptes/<str:compte_id>/capacites/", CapaciteUpdateView.as_view(), name="capacites"),
]
