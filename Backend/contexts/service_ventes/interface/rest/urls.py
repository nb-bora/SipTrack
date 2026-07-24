"""Routes REST du contexte Service & Ventes."""

from __future__ import annotations

from django.urls import path

from .views import ServiceDetailView, ServiceListCreateView, VenteCreateView

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
]
