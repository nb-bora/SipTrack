"""Implémentation Django du port Journal (append-only)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict

from contexts.service_ventes.infrastructure.django_app.models import MouvementModel
from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id


class DjangoJournal:
    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None:
        for evenement in evenements:
            MouvementModel.objects.create(
                id=new_id(),
                type=type(evenement).__name__,
                auteur_id=auteur_id,
                donnees=asdict(evenement),
                horodatage_saisie=evenement.occurred_on,
            )
