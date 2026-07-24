"""Configuration de l'app Django du contexte Service & Ventes.

L'app Django est un détail d'infrastructure interne au bounded context.
"""

from __future__ import annotations

from django.apps import AppConfig


class ServiceVentesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contexts.service_ventes.infrastructure.django_app"
    label = "service_ventes"
    verbose_name = "Service & Ventes"
