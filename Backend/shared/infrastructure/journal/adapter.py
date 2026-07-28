"""Implémentation Django du port Journal (append-only, chaîné)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict

from django.db import connection

from shared.domain.events import DomainEvent
from shared.domain.identifiers import new_id
from shared.infrastructure.journal.empreinte import GENESE, calculer_empreinte
from shared.infrastructure.journal.models import MouvementModel

# Identifiant arbitraire mais stable du verrou d'écriture du journal.
_VERROU_JOURNAL = 0x510_7 * 1_000


class DjangoJournal:
    def enregistrer(self, evenements: Iterable[DomainEvent], *, auteur_id: str) -> None:
        evenements = list(evenements)
        if not evenements:
            return

        self._verrouiller_la_chaine()
        precedent = MouvementModel.objects.order_by("-sequence").first()
        sequence = precedent.sequence if precedent is not None else 0
        empreinte_precedente = precedent.empreinte if precedent is not None else GENESE

        for evenement in evenements:
            sequence += 1
            identifiant = new_id()
            donnees = asdict(evenement)
            empreinte = calculer_empreinte(
                identifiant=identifiant,
                type_evenement=type(evenement).__name__,
                auteur_id=auteur_id,
                donnees=donnees,
                horodatage_saisie=evenement.occurred_on,
                sequence=sequence,
                empreinte_precedente=empreinte_precedente,
            )
            MouvementModel.objects.create(
                id=identifiant,
                sequence=sequence,
                type=type(evenement).__name__,
                auteur_id=auteur_id,
                donnees=donnees,
                horodatage_saisie=evenement.occurred_on,
                empreinte=empreinte,
                empreinte_precedente=empreinte_precedente,
            )
            empreinte_precedente = empreinte

    def _verrouiller_la_chaine(self) -> None:
        """Sérialise les écritures concurrentes.

        Sans ce verrou, deux services simultanés (deux bars, deux serveuses)
        liraient le même « dernier Mouvement » et produiraient deux branches
        avec la même `empreinte_precedente`. Le verrou est tenu jusqu'à la fin
        de la transaction en cours, donc libéré par le commit de l'Unit of Work.
        """
        with connection.cursor() as curseur:
            curseur.execute("SELECT pg_advisory_xact_lock(%s)", [_VERROU_JOURNAL])
