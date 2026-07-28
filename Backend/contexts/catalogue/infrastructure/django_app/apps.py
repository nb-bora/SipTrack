"""Application Django du contexte Catalogue."""

from django.apps import AppConfig


class CatalogueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contexts.catalogue.infrastructure.django_app"
    label = "catalogue"
