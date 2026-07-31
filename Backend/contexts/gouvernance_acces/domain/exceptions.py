"""Erreurs métier du contexte Gouvernance & Accès."""

from __future__ import annotations


class GouvernanceError(Exception):
    """Erreur de base du contexte."""


class BarIntrouvable(GouvernanceError):
    """Le bar n'existe pas."""

    def __init__(self, bar_id: str) -> None:
        super().__init__(f"Bar introuvable : {bar_id}.")
        self.bar_id = bar_id


class BarDejaExistant(GouvernanceError):
    """Ce bar a déjà été créé par ce propriétaire."""

    def __init__(self, nom: str) -> None:
        super().__init__(f"Un bar nommé « {nom} » existe déjà.")
        self.nom = nom


class CompteIntrouvable(GouvernanceError):
    """Le compte utilisateur n'existe pas."""

    def __init__(self, compte_id: str) -> None:
        super().__init__(f"Compte introuvable : {compte_id}.")
        self.compte_id = compte_id


class CompteDejaExistant(GouvernanceError):
    """Cet utilisateur a déjà un compte dans ce bar."""

    def __init__(self, bar_id: str, user_id: str) -> None:
        super().__init__(f"Un compte existe déjà pour {user_id} dans le bar {bar_id}.")
        self.bar_id = bar_id
        self.user_id = user_id


class CapaciteIntrouvable(GouvernanceError):
    """Cette capacité n'existe pas."""

    def __init__(self, capacite: str) -> None:
        super().__init__(f"Capacité introuvable : {capacite}.")
        self.capacite = capacite


class CapaciteDejaAccordée(GouvernanceError):
    """Ce compte possède déjà cette capacité."""

    def __init__(self, compte_id: str, capacite: str) -> None:
        super().__init__(f"{compte_id} possède déjà la capacité {capacite}.")
        self.compte_id = compte_id
        self.capacite = capacite


class CapaciteNonAccordée(GouvernanceError):
    """Le compte ne possède pas cette capacité."""

    def __init__(self, compte_id: str, capacite: str) -> None:
        super().__init__(f"{compte_id} ne possède pas la capacité {capacite}.")
        self.compte_id = compte_id
        self.capacite = capacite


class AutoriseNonAutorisé(GouvernanceError):
    """Un compte tente d'accorder une capacité qu'il n'a pas.

    Invariant : nul ne peut déléguer plus que ce qu'il possède.
    """

    def __init__(self, auteur_id: str, capacite: str) -> None:
        super().__init__(f"{auteur_id} n'a pas la capacité {capacite} pour la déléguer.")
        self.auteur_id = auteur_id
        self.capacite = capacite


class AccesDenie(GouvernanceError):
    """Un utilisateur tente d'accéder à un bar auquel il n'appartient pas.

    Cloisonnement strict appliqué à chaque requête.
    """

    def __init__(self, user_id: str, bar_id: str) -> None:
        super().__init__(f"{user_id} n'a pas accès au bar {bar_id}.")
        self.user_id = user_id
        self.bar_id = bar_id


class CapaciteRequiseManquante(GouvernanceError):
    """Un compte tente une opération sans en avoir la capacité.

    Le refus vient du système de droits, pas d'une validation métier.
    """

    def __init__(self, compte_id: str, capacite_requise: str, operation: str) -> None:
        super().__init__(
            f"{compte_id} n'a pas la capacité « {capacite_requise} » pour {operation}."
        )
        self.compte_id = compte_id
        self.capacite_requise = capacite_requise
        self.operation = operation


class UtilisateurIntrouvable(GouvernanceError):
    """Aucun utilisateur Django ne correspond à cet identifiant."""

    def __init__(self, user_id: str) -> None:
        super().__init__(f"Utilisateur introuvable : {user_id}.")
        self.user_id = user_id


class MotDePasseInvalide(GouvernanceError):
    """Le mot de passe ne satisfait pas les règles de validation."""

    def __init__(self, messages: list[str]) -> None:
        super().__init__(f"Mot de passe invalide : {' ; '.join(messages)}")
        self.messages = messages
