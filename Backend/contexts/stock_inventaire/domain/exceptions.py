"""Exceptions métier du contexte Stock & Inventaire."""


class ProduitIntrouvable(Exception):
    """Levée si un produit n'existe pas."""

    def __init__(self, produit_id: str) -> None:
        super().__init__(f"Produit {produit_id} introuvable")


class ProduitDejaExistant(Exception):
    """Levée si un produit de ce nom existe déjà dans le bar."""

    def __init__(self, bar_id: str, nom: str) -> None:
        super().__init__(f"Produit '{nom}' existe déjà dans le bar {bar_id}")


class QuantiteInsuffisante(Exception):
    """Levée si la quantité disponible ne suffit pas pour la vente."""

    def __init__(self, produit_id: str, disponible: int, demandee: int) -> None:
        super().__init__(f"Produit {produit_id}: {disponible} disponible, {demandee} demandée")


class QuantiteNegative(Exception):
    """Levée si une quantité doit devenir négative."""

    def __init__(self, produit_id: str, operation: str) -> None:
        super().__init__(f"Produit {produit_id}: {operation} rendrait la quantité négative")
