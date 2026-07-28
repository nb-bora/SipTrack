"""Routes REST du contexte Gouvernance & Accès."""

from __future__ import annotations

from django.urls import path

from .views import ObtenirJetonView

urlpatterns = [
    path("auth/jeton/", ObtenirJetonView.as_view(), name="obtenir-jeton"),
]
