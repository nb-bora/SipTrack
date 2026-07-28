"""Routes REST du contexte Service & Ventes."""

from __future__ import annotations

from django.urls import path

from .views import (
    AdditionDetailView,
    AdditionListCreateView,
    CloturerServiceView,
    PaiementCreateView,
    ReglementAdditionView,
    ServiceDetailView,
    ServiceListCreateView,
    SousCaisseListView,
    VenteCreateView,
    VersementCreateView,
)

urlpatterns = [
    path("services/", ServiceListCreateView.as_view(), name="service-list-create"),
    path(
        "services/<str:service_id>/",
        ServiceDetailView.as_view(),
        name="service-detail",
    ),
    path(
        "services/<str:service_id>/ventes/",
        VenteCreateView.as_view(),
        name="vente-create",
    ),
    path(
        "services/<str:service_id>/cloture/",
        CloturerServiceView.as_view(),
        name="service-cloture",
    ),
    path(
        "services/<str:service_id>/versement/",
        VersementCreateView.as_view(),
        name="versement-create",
    ),
    path(
        "services/<str:service_id>/sous-caisses/",
        SousCaisseListView.as_view(),
        name="sous-caisse-list",
    ),
    path(
        "services/<str:service_id>/additions/",
        AdditionListCreateView.as_view(),
        name="addition-list-create",
    ),
    path(
        "services/<str:service_id>/additions/<str:addition_id>/",
        AdditionDetailView.as_view(),
        name="addition-detail",
    ),
    path(
        "services/<str:service_id>/additions/<str:addition_id>/paiements/",
        PaiementCreateView.as_view(),
        name="paiement-create",
    ),
    path(
        "services/<str:service_id>/additions/<str:addition_id>/reglement/",
        ReglementAdditionView.as_view(),
        name="reglement-addition",
    ),
]
