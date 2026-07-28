"""Configuration Django app pour Stock & Inventaire."""

from django.apps import AppConfig


class StockInventaireConfig(AppConfig):
    """Configuration de l'application Stock & Inventaire."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "contexts.stock_inventaire.infrastructure.django_app"
    label = "stock_inventaire"
