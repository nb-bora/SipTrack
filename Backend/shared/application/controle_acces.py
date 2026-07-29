"""Qui a le droit d'agir, et où.

`shared.interface.rest.attribution` répond à « qui écrit ce fait ». Ce module
répond aux deux questions suivantes, qui ne se déduisent pas de la première :

- **Où** — un compte n'existe que dans un bar. Agir ailleurs n'a pas de sens.
- **Quoi** — un compte porte des capacités nommées. Le reste lui est fermé.

Le port vit dans `shared/` parce que tout contexte qui écrit un Fait doit
demander l'autorisation, et que le dupliquer par contexte garantirait qu'ils
divergent. Qui répond est branché par la composition root : les contextes ne se
connaissent pas (ADR-0005).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from shared.domain.attribution import Capacite


class CapaciteRequise(StrEnum):
    """Le nom de la capacité qu'un acte réclame, dit dans le langage commun.

    Gouvernance reste propriétaire de la définition des capacités
    (`CapaciteAtomique`). Ce miroir existe parce qu'une vue de Service & Ventes
    doit pouvoir *nommer* ce qu'elle exige sans importer Gouvernance (ADR-0005).

    Les deux listes ne peuvent pas diverger : `tests/test_autorisation.py` en
    vérifie l'égalité stricte. Ajouter une capacité d'un seul côté fait échouer
    la suite.
    """

    OUVRIR_SERVICE = "ouvrir_service"
    ENREGISTRER_VENTE = "enregistrer_vente"
    ENCAISSER = "encaisser"
    VERSER_RECETTE = "verser_recette"
    CLOTURER_SERVICE = "cloturer_service"

    CREER_CLIENT = "creer_client"
    ACCORDER_CREDIT = "accorder_credit"
    ENCAISSER_REMBOURSEMENT = "encaisser_remboursement"

    INSCRIRE_PRODUIT = "inscrire_produit"
    TARIFER = "tarifer"
    RETIRER_PRODUIT = "retirer_produit"

    CREER_COMPTE = "creer_compte"
    ACCORDER_CAPACITE = "accorder_capacite"
    RETIRER_CAPACITE = "retirer_capacite"
    COMPOSER_ROLE = "composer_role"
    DELEGUER = "deleguer"


class AccesRefuse(Exception):
    """L'appelant n'a pas le droit de faire cet acte dans ce bar.

    Une seule exception pour les deux refus — « pas de compte ici » et « pas
    cette capacité » — délibérément. Distinguer les deux dans la réponse
    apprendrait à un curieux quels bars existent et quelles capacités y sont
    accordées, alors qu'il n'a rien à y faire.
    """


class ControleAcces(Protocol):
    """Autoriser un acte, ou le refuser.

    **Deux méthodes, jamais une seule avec un drapeau.** Un privilège de
    consultation — celui des comptes plateforme — s'attache à `exiger_lecture`
    et à lui seul. Tant que les deux chemins sont distincts, aucune écriture ne
    peut l'atteindre, même par erreur de programmation : il n'y a pas de valeur
    de paramètre qui fasse basculer l'un dans l'autre.

    Ne renvoient rien d'exploitable en cas de refus : soit l'acte est permis et
    l'appel passe, soit il lève. Un booléen se serait ignoré par oubli — une
    exception, non.
    """

    def exiger_lecture(self, *, auteur_id: str, bar_id: str, operation: str) -> None:
        """Lève `AccesRefuse` si l'auteur ne peut pas consulter ce bar.

        Appartenir au bar suffit : aucune capacité de lecture n'existe dans
        l'énumération, et en inventer une par endpoint donnerait une liste que
        personne ne tiendrait à jour.
        """
        ...

    def exiger_capacite(
        self, *, auteur_id: str, bar_id: str, capacite: str, operation: str
    ) -> Capacite:
        """Lève `AccesRefuse` si l'auteur ne peut pas faire cet acte dans ce bar.

        `operation` est le libellé métier de l'acte (« clôturer le service »),
        destiné au message d'erreur. Il n'entre pas dans la décision.

        Rend la **qualité** en laquelle l'auteur agit. Le compte vient d'être
        chargé pour décider ; la déduire au passage évite à l'appelant une
        seconde recherche identique — mesurée, elle avait bel et bien lieu.
        """
        ...
