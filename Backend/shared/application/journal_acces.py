"""Trace des consultations exercées au titre du privilège plateforme.

Un compte plateforme peut lire n'importe quel bar. Cette faculté n'est tenable
qu'à une condition : que le propriétaire du bar puisse voir **quand** on a
regardé ses données. « Je peux voir vos données, et vous voyez quand je les
regarde » se défend. « Je peux tout voir sans que vous le sachiez » ne se
défend pas.

Pourquoi une table à part, et non le journal métier : `DjangoJournal.enregistrer`
prend un verrou global à toute la plateforme pour garantir le chaînage des
empreintes. Une requête `GET` de support y aurait bloqué les écritures de tous
les autres établissements. Et une consultation n'est pas un Fait d'exploitation :
aucun stock ne bouge, aucun argent ne circule.
"""

from __future__ import annotations

from typing import Protocol


class JournalDesAcces(Protocol):
    """Inscrire une consultation faite au titre du privilège plateforme.

    N'est appelé que lorsque le privilège a **réellement servi** — c'est-à-dire
    quand le lecteur n'avait pas de compte dans ce bar. Une gérante consultant
    son propre bar ne produit aucune écriture ici.
    """

    def consultation(self, *, administrateur_id: str, bar_id: str, operation: str) -> None:
        """Enregistre l'accès. Ne lève pas : refuser la trace ne doit pas refuser le service."""
        ...
