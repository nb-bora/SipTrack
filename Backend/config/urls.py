"""Routage racine du projet.

Chaque bounded context expose ses routes via sa couche interface.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView as VueSchema
from drf_spectacular.views import SpectacularRedocView, SpectacularSwaggerView

from shared.interface.rest.permissions import AccesDocumentation

_ACCES_DOC = [AccesDocumentation]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("contexts.gouvernance_acces.interface.rest.urls")),
    path("api/", include("contexts.service_ventes.interface.rest.urls")),
    path("api/", include("contexts.credit_creances.interface.rest.urls")),
    path("api/", include("contexts.catalogue.interface.rest.urls")),
    path("api/", include("contexts.stock_inventaire.interface.rest.urls")),
    # --- Documentation de l'API ---
    path(
        "api/schema/",
        VueSchema.as_view(permission_classes=_ACCES_DOC),
        name="schema",
    ),
    path(
        "api/doc/",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=_ACCES_DOC),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema", permission_classes=_ACCES_DOC),
        name="redoc",
    ),
]
