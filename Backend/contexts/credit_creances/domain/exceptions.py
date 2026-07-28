"""Erreurs métier du contexte Crédit & Créances."""

from __future__ import annotations


class CreditCreancesError(Exception):
    """Erreur de base du contexte."""


class ClientIntrouvable(CreditCreancesError):
    """Aucun client ne correspond à l'identifiant fourni."""

    def __init__(self, client_id: str) -> None:
        super().__init__(f"Client introuvable : {client_id}.")
        self.client_id = client_id


class CreditIntrouvable(CreditCreancesError):
    """Aucun crédit ne correspond à l'identifiant fourni."""

    def __init__(self, credit_id: str) -> None:
        super().__init__(f"Crédit introuvable : {credit_id}.")
        self.credit_id = credit_id


class CreditDejaSolde(CreditCreancesError):
    """Remboursement refusé : la créance est éteinte.

    Nommée `CreditDejaSolde` et non `CreditSolde` : ce dernier est l'**événement**
    qui célèbre l'extinction de la dette. Confondre les deux dans le journal
    rendrait illisible ce qui s'est réellement passé.
    """

    def __init__(self, credit_id: str) -> None:
        super().__init__(f"Le crédit {credit_id} est déjà soldé.")
        self.credit_id = credit_id


class RemboursementSuperieurAuReste(CreditCreancesError):
    """Remboursement refusé : il dépasse ce qui reste dû.

    Rendre la monnaie sur un remboursement est un autre Fait ; l'absorber
    silencieusement transformerait un trop-perçu en cadeau invisible.
    """

    def __init__(self, credit_id: str, reste: int) -> None:
        super().__init__(f"Le crédit {credit_id} ne doit plus que {reste}.")
        self.credit_id = credit_id
        self.reste = reste


class CreditDejaOuvertPourCetteAddition(CreditCreancesError):
    """Une addition ne peut engendrer qu'une seule créance.

    Deux créances pour la même consommation feraient payer le client deux fois.
    """

    def __init__(self, addition_id: str) -> None:
        super().__init__(f"L'addition {addition_id} a déjà donné lieu à un crédit.")
        self.addition_id = addition_id
