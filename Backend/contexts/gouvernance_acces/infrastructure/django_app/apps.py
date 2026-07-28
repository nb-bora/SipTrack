"""Configuration Django du contexte Gouvernance."""

from django.apps import AppConfig


class GouvernanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contexts.gouvernance_acces.infrastructure.django_app"
    label = "gouvernance"
