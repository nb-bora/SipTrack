"""Routage racine du projet.

Chaque bounded context expose ses routes via sa couche interface.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("contexts.service_ventes.interface.rest.urls")),
]
