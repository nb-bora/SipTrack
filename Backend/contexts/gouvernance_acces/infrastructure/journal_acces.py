"""Adaptateur : inscription des consultations plateforme."""

from __future__ import annotations

import logging

from shared.domain.identifiers import new_id

from .django_app.models import AccesPlateformeModel

_logger = logging.getLogger(__name__)


class DjangoJournalDesAcces:
    """Insertion simple, hors du verrou de chaînage du journal métier."""

    def consultation(self, *, administrateur_id: str, bar_id: str, operation: str) -> None:
        """Enregistre l'accès sans jamais faire échouer la requête qu'il trace.

        Le compromis est assumé et il va dans ce sens-là : une trace perdue est
        un incident, un support incapable de lire pendant une panne d'écriture
        en est un plus grave. L'échec est journalisé en `error` pour qu'il ne
        passe pas inaperçu.
        """
        try:
            AccesPlateformeModel.objects.create(
                id=new_id(),
                administrateur_id=administrateur_id,
                bar_id=bar_id,
                operation=operation,
            )
        except Exception:  # noqa: BLE001 — voir la docstring : on trace, on ne bloque pas.
            _logger.exception(
                "Consultation plateforme non tracée",
                extra={"administrateur_id": administrateur_id, "bar_id": bar_id},
            )
