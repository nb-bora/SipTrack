"""Cas d'usage : inscription publique — créer un compte et un premier bar."""

from __future__ import annotations

from django.contrib.auth import get_user_model

from contexts.gouvernance_acces.application.dto import (
    BarDTO,
    InscrireUtilisateurCommand,
)
from contexts.gouvernance_acces.domain.bar import Bar
from contexts.gouvernance_acces.domain.compte import Compte
from contexts.gouvernance_acces.domain.enums import CapaciteAtomique
from contexts.gouvernance_acces.domain.repositories import (
    BarRepository,
    CompteRepository,
)
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork

User = get_user_model()


class UtilisateurDejaInscrit(Exception):
    """Tentative de créer un compte avec un username déjà utilisé."""


class InscrireUtilisateurHandler:
    """Inscription publique : crée un utilisateur et son premier bar."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        bars: BarRepository,
        comptes: CompteRepository,
        journal: Journal,
    ) -> None:
        self._uow = uow
        self._bars = bars
        self._comptes = comptes
        self._journal = journal

    def inscrire(self, commande: InscrireUtilisateurCommand) -> tuple[BarDTO, str]:
        """Crée un utilisateur, son premier bar, et un compte avec capacités pleines.

        Retourne (bar, user_id) que le client peut utiliser pour obtenir un jeton.
        """
        with self._uow:
            # Vérifier que le username n'existe pas
            if User.objects.filter(username=commande.username).exists():
                raise UtilisateurDejaInscrit(commande.username)

            # Créer l'utilisateur
            user = User.objects.create_user(
                username=commande.username,
                email=commande.email,
                password=commande.password,
            )
            user_id = str(user.pk)

            # Créer le bar
            bar = Bar.creer(
                nom=commande.nom_bar,
                proprietaire_id=user_id,
            )
            self._bars.ajouter(bar)
            self._journal.enregistrer(bar.evenements_non_publies(), auteur_id=user_id)
            bar.purger_evenements()

            # Créer le compte avec capacités pleines (bootstrapping)
            compte = Compte.creer(
                bar_id=bar.id,
                user_id=user_id,
                capacites_initiales=CapaciteAtomique.toutes(),
                auteur_id=user_id,
            )
            self._comptes.ajouter(compte)
            self._journal.enregistrer(compte.evenements_non_publies(), auteur_id=user_id)
            compte.purger_evenements()

            self._uow.commit()

            return BarDTO.depuis_bar(bar), user_id
