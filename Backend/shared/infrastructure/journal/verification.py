"""Vérification de l'intégrité du journal.

Rejoue la chaîne d'empreintes du début à la fin et signale la première ligne
qui ne correspond pas à ce qui a été signé au fil de l'eau. C'est ce qui donne
sa valeur au chaînage : sans vérification, une empreinte n'est qu'une colonne
de plus.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.infrastructure.journal.empreinte import GENESE, calculer_empreinte
from shared.infrastructure.journal.models import MouvementModel


@dataclass(frozen=True)
class Anomalie:
    sequence: int
    mouvement_id: str
    motif: str


def verifier_journal() -> list[Anomalie]:
    """Renvoie les anomalies détectées, dans l'ordre du journal. Vide = intègre."""
    anomalies: list[Anomalie] = []
    attendu_precedent = GENESE
    sequence_attendue = 1

    for mouvement in MouvementModel.objects.order_by("sequence").iterator():
        if mouvement.sequence != sequence_attendue:
            anomalies.append(
                Anomalie(
                    sequence=mouvement.sequence,
                    mouvement_id=mouvement.id,
                    motif=(
                        f"séquence {mouvement.sequence} là où {sequence_attendue} "
                        "était attendue — un Mouvement manque ou a été inséré"
                    ),
                )
            )
            sequence_attendue = mouvement.sequence

        if mouvement.empreinte_precedente != attendu_precedent:
            anomalies.append(
                Anomalie(
                    sequence=mouvement.sequence,
                    mouvement_id=mouvement.id,
                    motif="la chaîne est rompue : ce Mouvement ne suit pas le précédent",
                )
            )

        recalculee = calculer_empreinte(
            identifiant=mouvement.id,
            type_evenement=mouvement.type,
            auteur_id=mouvement.auteur_id,
            donnees=mouvement.donnees,
            horodatage_saisie=mouvement.horodatage_saisie,
            sequence=mouvement.sequence,
            empreinte_precedente=mouvement.empreinte_precedente,
        )
        if recalculee != mouvement.empreinte:
            anomalies.append(
                Anomalie(
                    sequence=mouvement.sequence,
                    mouvement_id=mouvement.id,
                    motif="le contenu ne correspond plus à son empreinte — Mouvement altéré",
                )
            )

        attendu_precedent = mouvement.empreinte
        sequence_attendue += 1

    return anomalies
