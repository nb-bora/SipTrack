"""Adaptateur : Gouvernance répond à la question « a-t-il le droit ? ».

Ce contexte est le seul à savoir ce qu'est un compte et ce qu'est une capacité.
Les autres posent la question par le port `shared.application.controle_acces`
sans jamais l'importer (ADR-0005) : la composition root branche cet adaptateur
derrière le port.
"""

from __future__ import annotations

from contexts.gouvernance_acces.domain.enums import CapaciteAtomique
from contexts.gouvernance_acces.domain.exceptions import CapaciteRequiseManquante
from contexts.gouvernance_acces.domain.repositories import CompteRepository
from shared.application.controle_acces import AccesRefuse
from shared.domain.attribution import Capacite


class ControleAccesParCompte:
    """Autorise d'après le compte que l'appelant possède **dans ce bar**.

    Le cloisonnement ne demande aucun test supplémentaire : il tombe de la
    recherche elle-même. Un compte n'existe que pour un couple (bar, utilisateur)
    — chercher celui de l'appelant dans un bar où il n'a rien à faire ne trouve
    rien, et rien vaut refus.
    """

    def __init__(self, comptes: CompteRepository) -> None:
        self._comptes = comptes

    def exiger(self, *, auteur_id: str, bar_id: str, capacite: str | None, operation: str) -> None:
        """Lève `AccesRefuse` si l'auteur ne peut pas faire cet acte dans ce bar."""
        if capacite is not None and not CapaciteAtomique.valide(capacite):
            # Une capacité mal orthographiée dans un appelant ne doit pas devenir
            # un refus silencieux qu'on mettrait des heures à comprendre : c'est
            # un défaut de programmation, pas une décision d'autorisation.
            raise ValueError(f"Capacité inconnue : {capacite}")

        compte = self._comptes.du_bar_et_user(bar_id=bar_id, user_id=auteur_id)
        if compte is None:
            raise AccesRefuse(f"Aucun compte pour {operation} dans ce bar.")

        if capacite is None:
            return

        try:
            compte.verifier_capacite(capacite, operation)
        except CapaciteRequiseManquante as manque:
            # Traduit vers le vocabulaire partagé : les autres contextes ne
            # connaissent pas les exceptions de Gouvernance.
            raise AccesRefuse(str(manque)) from manque

    def qualite(self, *, auteur_id: str, bar_id: str) -> Capacite:
        """Supervision dès lors que la personne peut clôturer un service.

        Clôturer est l'acte qui fige les écarts de la soirée : qui en répond
        supervise, par définition. Le reste est de l'opération. La règle est
        volontairement tirée d'une capacité réelle plutôt que d'un champ envoyé
        avec la requête — c'est tout l'objet du changement.
        """
        compte = self._comptes.du_bar_et_user(bar_id=bar_id, user_id=auteur_id)
        if compte is None:
            raise AccesRefuse("Aucun compte dans ce bar.")

        if compte.possede(CapaciteAtomique.CLOTURER_SERVICE):
            return Capacite.SUPERVISEUSE
        return Capacite.OPERATRICE
