"""Routes REST du contexte Service & Ventes."""

from __future__ import annotations

from django.urls import path

from .views import (
    AdditionListCreateView,
    CloturerServiceView,
    ServiceDetailView,
    ServiceListCreateView,
    VenteCreateView,
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
        "services/<str:service_id>/additions/",
        AdditionListCreateView.as_view(),
        name="addition-list-create",
    ),
]
