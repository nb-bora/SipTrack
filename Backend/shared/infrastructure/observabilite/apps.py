"""Application Django de l'observabilité technique."""

from __future__ import annotations

from django.apps import AppConfig


class ObservabiliteConfig(AppConfig):
    name = "shared.infrastructure.observabilite"
    label = "observabilite"
    verbose_name = "Observabilité technique"
