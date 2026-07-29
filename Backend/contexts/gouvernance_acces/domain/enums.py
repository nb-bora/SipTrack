"""Énumérations du contexte Gouvernance.

Les capacités sont **atomiques** — chaque opération du système requiert au moins
une. Une gérante les combine en rôles, nommés en métier, composables à sa guise.
"""

from enum import StrEnum


class CapaciteAtomique(StrEnum):
    """Chaque acte du système suppose une capacité.

    Nommées en métier (« encaisser »), jamais en technique (« POST /paiements »).
    Une gérante doit pouvoir lire « ma serveuse peut encaisser ».
    """

    # === Service & Ventes ===
    OUVRIR_SERVICE = "ouvrir_service"
    ENREGISTRER_VENTE = "enregistrer_vente"
    ENCAISSER = "encaisser"  # forme_paiement : especes, credit, mobile_money
    VERSER_RECETTE = "verser_recette"
    CLOTURER_SERVICE = "cloturer_service"

    # === Crédit & Créances ===
    CREER_CLIENT = "creer_client"
    ACCORDER_CREDIT = "accorder_credit"
    ENCAISSER_REMBOURSEMENT = "encaisser_remboursement"

    # === Catalogue ===
    INSCRIRE_PRODUIT = "inscrire_produit"
    TARIFER = "tarifer"
    RETIRER_PRODUIT = "retirer_produit"

    # === Gouvernance (auto-référentiel) ===
    CREER_COMPTE = "creer_compte"
    ACCORDER_CAPACITE = "accorder_capacite"
    RETIRER_CAPACITE = "retirer_capacite"
    COMPOSER_ROLE = "composer_role"
    DELEGUER = "deleguer"

    # === Pas dans la tranche actuelle (Stock, Approvisionnement, etc.) ===
    # ENREGISTRER_MOUVEMENT_STOCK = "enregistrer_mouvement_stock"
    # FAIRE_INVENTAIRE = "faire_inventaire"

    @classmethod
    def toutes(cls) -> frozenset[str]:
        """Toutes les capacités définies."""
        return frozenset(c.value for c in cls)

    @classmethod
    def valide(cls, nom: str) -> bool:
        """Vérifie qu'une chaîne nomme une capacité réelle."""
        return nom in cls.toutes()


class CapacitePlateforme(StrEnum):
    """Ce qu'un compte plateforme peut faire — sur un axe **distinct** des bars.

    Volontairement séparé de `CapaciteAtomique` : les deux ne se mélangent
    jamais. Un jeu de droits plateforme ne doit pas pouvoir satisfaire par
    accident un contrôle d'exploitation, et réciproquement.

    Aucune capacité d'écriture dans un bar n'y figure, et il ne faut pas en
    ajouter. Un compte capable d'écrire dans le journal de n'importe quel bar
    rendrait ce journal contestable : en litige, la défense deviendrait « un
    compte de la plateforme a pu écrire ce mouvement », et la chaîne
    d'empreintes ne prouverait plus rien.
    """

    # Consulter n'importe quel bar, pour le support. Chaque consultation exercée
    # à ce titre est inscrite au journal des accès, visible du propriétaire.
    LIRE_TOUT_BAR = "lire_tout_bar"

    # Administration de la plateforme, hors exploitation d'un bar.
    CREER_BAR = "creer_bar_plateforme"
    SUSPENDRE_BAR = "suspendre_bar"
    GERER_FACTURATION = "gerer_facturation"

    @classmethod
    def toutes(cls) -> frozenset[str]:
        return frozenset(c.value for c in cls)

    @classmethod
    def valide(cls, nom: str) -> bool:
        return nom in cls.toutes()
