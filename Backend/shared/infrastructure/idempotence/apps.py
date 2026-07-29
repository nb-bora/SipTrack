"""Application Django de l'idempotence des écritures."""

from __future__ import annotations

from django.apps import AppConfig


class IdempotenceConfig(AppConfig):
    name = "shared.infrastructure.idempotence"
    label = "idempotence"
    verbose_name = "Idempotence des écritures"
