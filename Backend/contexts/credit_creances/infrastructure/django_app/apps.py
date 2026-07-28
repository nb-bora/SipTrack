"""Configuration de l'application Django pour le contexte Créances."""

from django.apps import AppConfig


class CreditCreancesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contexts.credit_creances.infrastructure.django_app"
    label = "credit_creances"
