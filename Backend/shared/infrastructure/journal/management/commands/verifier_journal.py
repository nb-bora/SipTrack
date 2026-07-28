"""Vérifie l'intégrité du journal des Mouvements."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from shared.infrastructure.journal.models import MouvementModel
from shared.infrastructure.journal.verification import verifier_journal


class Command(BaseCommand):
    help = "Rejoue la chaîne d'empreintes du journal et signale toute altération."

    def handle(self, *args: Any, **options: Any) -> None:
        total = MouvementModel.objects.count()
        anomalies = verifier_journal()

        if not anomalies:
            self.stdout.write(
                self.style.SUCCESS(f"Journal intègre — {total} Mouvement(s) vérifié(s).")
            )
            return

        for anomalie in anomalies:
            self.stdout.write(
                self.style.ERROR(
                    f"#{anomalie.sequence} ({anomalie.mouvement_id}) : {anomalie.motif}"
                )
            )
        # Sortie non nulle : utilisable dans une tâche planifiée ou un contrôle.
        raise CommandError(f"{len(anomalies)} anomalie(s) sur {total} Mouvement(s).")
