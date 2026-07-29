"""Adaptateur : Gouvernance répond à la question « a-t-il le droit ? ».

Ce contexte est le seul à savoir ce qu'est un compte et ce qu'est une capacité.
Les autres posent la question par le port `shared.application.controle_acces`
sans jamais l'importer (ADR-0005) : la composition root branche cet adaptateur
derrière le port.
"""

from __future__ import annotations

from contexts.gouvernance_acces.domain.enums import CapaciteAtomique, CapacitePlateforme
from contexts.gouvernance_acces.domain.exceptions import CapaciteRequiseManquante
from contexts.gouvernance_acces.domain.repositories import CompteRepository
from shared.application.controle_acces import AccesRefuse
from shared.application.journal_acces import JournalDesAcces
from shared.domain.attribution import Capacite


class ControleAccesParCompte:
    """Autorise d'après le compte que l'appelant possède **dans ce bar**.

    Le cloisonnement ne demande aucun test supplémentaire : il tombe de la
    recherche elle-même. Un compte n'existe que pour un couple (bar, utilisateur)
    — chercher celui de l'appelant dans un bar où il n'a rien à faire ne trouve
    rien, et rien vaut refus.

    **Une seule dérogation, et elle ne touche que la lecture** : un compte
    plateforme portant `lire_tout_bar` consulte n'importe quel bar. Elle vit dans
    `exiger_lecture` et nulle part ailleurs — `exiger_capacite` ne la connaît
    pas, donc aucune écriture ne peut l'atteindre, quelle que soit la façon dont
    on l'appelle.
    """

    def __init__(self, comptes: CompteRepository, acces: JournalDesAcces) -> None:
        self._comptes = comptes
        self._acces = acces

    def exiger_lecture(self, *, auteur_id: str, bar_id: str, operation: str) -> None:
        """Lève `AccesRefuse` si l'auteur ne peut pas consulter ce bar."""
        if self._comptes.du_bar_et_user(bar_id=bar_id, user_id=auteur_id) is not None:
            # Chemin courant : la personne travaille ici. Rien à tracer — le
            # journal des accès répond à « qui d'*extérieur* a regardé », et le
            # noyer sous les lectures ordinaires le rendrait illisible.
            return

        if not self._est_administrateur_lecteur(auteur_id):
            raise AccesRefuse(f"Aucun compte pour {operation} dans ce bar.")

        # Le privilège a réellement servi : il laisse une trace, visible du
        # propriétaire du bar. C'est la contrepartie qui le rend acceptable.
        self._acces.consultation(administrateur_id=auteur_id, bar_id=bar_id, operation=operation)

    def exiger_capacite(
        self, *, auteur_id: str, bar_id: str, capacite: str, operation: str
    ) -> Capacite:
        """Lève `AccesRefuse` si l'auteur ne peut pas faire cet acte dans ce bar.

        Aucune dérogation ici, et il ne faut pas en ajouter : un compte capable
        d'écrire dans le journal de n'importe quel bar rendrait ce journal
        contestable.
        """
        if not CapaciteAtomique.valide(capacite):
            # Une capacité mal orthographiée dans un appelant ne doit pas devenir
            # un refus silencieux qu'on mettrait des heures à comprendre : c'est
            # un défaut de programmation, pas une décision d'autorisation.
            raise ValueError(f"Capacité inconnue : {capacite}")

        compte = self._comptes.du_bar_et_user(bar_id=bar_id, user_id=auteur_id)
        if compte is None:
            raise AccesRefuse(f"Aucun compte pour {operation} dans ce bar.")

        try:
            compte.verifier_capacite(capacite, operation)
        except CapaciteRequiseManquante as manque:
            # Traduit vers le vocabulaire partagé : les autres contextes ne
            # connaissent pas les exceptions de Gouvernance.
            raise AccesRefuse(str(manque)) from manque

        # Supervision dès lors que la personne peut clôturer un service :
        # clôturer est l'acte qui fige les écarts de la soirée, donc qui en
        # répond supervise. Le reste est de l'opération.
        if compte.possede(CapaciteAtomique.CLOTURER_SERVICE):
            return Capacite.SUPERVISEUSE
        return Capacite.OPERATRICE

    @staticmethod
    def _est_administrateur_lecteur(user_id: str) -> bool:
        """Un compte plateforme actif, portant `lire_tout_bar`.

        Requête ne ramenant que les capacités, et **jamais atteinte** quand
        l'appelant a un compte dans le bar : le chemin courant reste à une seule
        recherche.
        """
        from contexts.gouvernance_acces.infrastructure.django_app.models import (
            AdministrateurPlateformeModel,
        )

        capacites = (
            AdministrateurPlateformeModel.objects.filter(user_id=user_id, actif=True)
            .values_list("capacites", flat=True)
            .first()
        )
        return capacites is not None and CapacitePlateforme.LIRE_TOUT_BAR in capacites
