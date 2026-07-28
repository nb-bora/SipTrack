"""Erreurs métier du contexte Catalogue."""

from __future__ import annotations


class CatalogueError(Exception):
    """Erreur de base du contexte."""


class ProduitIntrouvable(CatalogueError):
    """Aucun produit ne correspond à l'identifiant fourni."""

    def __init__(self, produit_id: str) -> None:
        super().__init__(f"Produit introuvable : {produit_id}.")
        self.produit_id = produit_id


class ProduitDejaInscrit(CatalogueError):
    """Ce nom existe déjà dans ce bar.

    Deux lignes pour la même bière rendraient tout comptage ambigu — et
    permettraient d'en tenir une à un prix minoré.
    """

    def __init__(self, bar_id: str, nom: str) -> None:
        super().__init__(f"« {nom} » figure déjà au catalogue du bar {bar_id}.")
        self.bar_id = bar_id
        self.nom = nom


class ProduitRetireDeLaVente(CatalogueError):
    """Vente refusée : ce produit ne se vend plus."""

    def __init__(self, produit_id: str) -> None:
        super().__init__(f"Le produit {produit_id} est retiré de la vente.")
        self.produit_id = produit_id


class TarifInchange(CatalogueError):
    """Changement refusé : le prix proposé est déjà le prix en vigueur.

    Écrire un Fait « le prix passe de 1 000 à 1 000 » polluerait le journal
    d'événements qui ne disent rien.
    """

    def __init__(self, produit_id: str, prix: int) -> None:
        super().__init__(f"Le produit {produit_id} est déjà à {prix}.")
        self.produit_id = produit_id
        self.prix = prix
