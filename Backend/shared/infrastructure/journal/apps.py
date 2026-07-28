"""Application Django du journal."""

from __future__ import annotations

from django.apps import AppConfig


class JournalConfig(AppConfig):
    name = "shared.infrastructure.journal"
    label = "journal"
    verbose_name = "Journal des Mouvements"
