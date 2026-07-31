"""Cas d'usage : créer et gérer les comptes, accorder/retirer des capacités."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from contexts.gouvernance_acces.application.dto import (
    AccorderCapaciteCommand,
    CompteDTO,
    CreerCompteCommand,
    CreerEmployeCommand,
    RetirerCapaciteCommand,
)
from contexts.gouvernance_acces.application.use_cases.inscrire_utilisateur import (
    UtilisateurDejaInscrit,
)
from contexts.gouvernance_acces.domain.compte import Compte
from contexts.gouvernance_acces.domain.enums import CapaciteAtomique
from contexts.gouvernance_acces.domain.exceptions import (
    AutoriseNonAutorisé,
    BarIntrouvable,
    CompteDejaExistant,
    CompteIntrouvable,
    MotDePasseInvalide,
    UtilisateurIntrouvable,
)
from contexts.gouvernance_acces.domain.repositories import (
    BarRepository,
    CompteRepository,
    ProfilRepository,
)
from shared.application.journal import Journal
from shared.application.unit_of_work import UnitOfWork

User = get_user_model()


class GererComptesHandler:
    """Créer des comptes utilisateurs et gérer leurs capacités."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        bars: BarRepository,
        comptes: CompteRepository,
        profils: ProfilRepository,
        journal: Journal,
    ) -> None:
        self._uow = uow
        self._bars = bars
        self._comptes = comptes
        self._profils = profils
        self._journal = journal

    def creer(self, commande: CreerCompteCommand) -> CompteDTO:
        """Crée un compte utilisateur dans un bar.

        Seule la gérante (qui a la capacité CREER_COMPTE) peut le faire.
        Les capacites initiales sont accordees ici, documentees dans le Fait.
        """
        with self._uow:
            # Vérifier que le bar existe.
            bar = self._bars.par_id(commande.bar_id)
            if bar is None:
                raise BarIntrouvable(commande.bar_id)

            # Vérifier que l'utilisateur cible existe.
            if not User.objects.filter(pk=commande.user_id).exists():
                raise UtilisateurIntrouvable(commande.user_id)

            # Vérifier que l'auteur a CREER_COMPTE.
            auteur = self._charger_compte_auteur(commande.bar_id, commande.auteur_id)
            auteur.verifier_capacite(CapaciteAtomique.CREER_COMPTE, "créer un compte")

            # Vérifier qu'aucun compte n'existe déjà pour cet utilisateur.
            existant = self._comptes.du_bar_et_user(
                bar_id=commande.bar_id, user_id=commande.user_id
            )
            if existant is not None:
                raise CompteDejaExistant(commande.bar_id, commande.user_id)

            return self._creer_compte_pour(
                bar_id=commande.bar_id,
                user_id=commande.user_id,
                capacites_initiales=commande.capacites_initiales,
                auteur_id=commande.auteur_id,
            )

    def _creer_compte_pour(
        self,
        *,
        bar_id: str,
        user_id: str,
        capacites_initiales: frozenset[str],
        auteur_id: str,
    ) -> CompteDTO:
        """Crée un compte utilisateur avec vérifications et persistance.

        Appellé par creer() et creer_employe().
        """
        # Vérifier que l'auteur a CREER_COMPTE.
        auteur = self._charger_compte_auteur(bar_id, auteur_id)
        auteur.verifier_capacite(CapaciteAtomique.CREER_COMPTE, "créer un compte")

        # Vérifier que l'auteur ne délègue que ce qu'il possède.
        for cap in capacites_initiales:
            if not CapaciteAtomique.valide(cap):
                raise ValueError(f"Capacité inconnue : {cap}")
            if not auteur.possede(cap):
                raise AutoriseNonAutorisé(auteur_id, cap)

        # Créer le compte avec les capacités initiales.
        compte = Compte.creer(
            bar_id=bar_id,
            user_id=user_id,
            capacites_initiales=capacites_initiales,
            auteur_id=auteur_id,
        )
        self._comptes.ajouter(compte)
        self._journal.enregistrer(compte.evenements_non_publies(), auteur_id=auteur_id)
        compte.purger_evenements()
        self._uow.commit()

        return CompteDTO.depuis_compte(compte)

    def accorder_capacite(self, commande: AccorderCapaciteCommand) -> CompteDTO:
        """Accorde une capacité à un compte.

        L'auteur doit avoir la capacité ACCORDER_CAPACITE et la capacité qu'il
        veut accorder.
        """
        with self._uow:
            compte = self._comptes.par_id(commande.compte_id)
            if compte is None:
                raise CompteIntrouvable(commande.compte_id)

            auteur = self._charger_compte_auteur(compte.bar_id, commande.auteur_id)
            auteur.verifier_capacite(CapaciteAtomique.ACCORDER_CAPACITE, "accorder une capacité")

            if not CapaciteAtomique.valide(commande.capacite):
                raise ValueError(f"Capacité inconnue : {commande.capacite}")

            if not auteur.possede(commande.capacite):
                raise AutoriseNonAutorisé(commande.auteur_id, commande.capacite)

            compte.accorder(capacite=commande.capacite, auteur_id=commande.auteur_id)
            self._comptes.mettre_a_jour(compte)
            self._journal.enregistrer(compte.evenements_non_publies(), auteur_id=commande.auteur_id)
            compte.purger_evenements()
            self._uow.commit()

            return CompteDTO.depuis_compte(compte)

    def retirer_capacite(self, commande: RetirerCapaciteCommand) -> CompteDTO:
        """Retire une capacité d'un compte."""
        with self._uow:
            compte = self._comptes.par_id(commande.compte_id)
            if compte is None:
                raise CompteIntrouvable(commande.compte_id)

            auteur = self._charger_compte_auteur(compte.bar_id, commande.auteur_id)
            auteur.verifier_capacite(CapaciteAtomique.RETIRER_CAPACITE, "retirer une capacité")

            compte.retirer(capacite=commande.capacite, auteur_id=commande.auteur_id)
            self._comptes.mettre_a_jour(compte)
            self._journal.enregistrer(compte.evenements_non_publies(), auteur_id=commande.auteur_id)
            compte.purger_evenements()
            self._uow.commit()

            return CompteDTO.depuis_compte(compte)

    def creer_employe(self, commande: CreerEmployeCommand) -> CompteDTO:
        """Crée un employé : d'abord l'utilisateur Django, puis le compte du bar.

        Le mot de passe est validé ; un mot de passe invalide lève MotDePasseInvalide.
        """
        with self._uow:
            # Vérifier que le username n'existe pas.
            if User.objects.filter(username=commande.username).exists():
                raise UtilisateurDejaInscrit(commande.username)

            # Vérifier que le bar existe.
            bar = self._bars.par_id(commande.bar_id)
            if bar is None:
                raise BarIntrouvable(commande.bar_id)

            # Valider le mot de passe.
            try:
                validate_password(commande.mot_de_passe_initial)
            except ValidationError as e:
                raise MotDePasseInvalide(e.messages) from e

            # Créer l'utilisateur Django.
            user = User.objects.create_user(
                username=commande.username,
                password=commande.mot_de_passe_initial,
            )
            user_id = str(user.pk)

            # Créer le profil avec flag "doit changer mot de passe".
            self._profils.creer_pour(user_id, doit_changer_mdp=True)

            # Créer le compte dans le bar.
            return self._creer_compte_pour(
                bar_id=commande.bar_id,
                user_id=user_id,
                capacites_initiales=commande.capacites_initiales,
                auteur_id=commande.auteur_id,
            )

    def _charger_compte_auteur(self, bar_id: str, user_id: str) -> Compte:
        """Charge le compte de l'auteur dans ce bar.

        Levée si le compte n'existe pas ou qu'il n'appartient pas à ce bar.
        """
        compte = self._comptes.du_bar_et_user(bar_id=bar_id, user_id=user_id)
        if compte is None:
            raise CompteIntrouvable(f"compte de {user_id} dans {bar_id}")
        return compte
