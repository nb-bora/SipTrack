"""Le garde posé devant chaque acte, à la frontière HTTP.

`attribution.auteur_id_de` dit **qui** écrit. Ce module dit **s'il a le droit** :
il consulte le port `ControleAcces` et traduit un refus en 403.

Deux gardes, jamais un seul :

- `exiger_lecture` — consulter. Suppose d'appartenir au bar.
- `exiger_capacite` — agir. Suppose une capacité nommée, accordée.

La séparation n'est pas cosmétique. Un paramètre unique valant tantôt « lecture »
tantôt « écriture » se remplit mal un jour de fatigue, et l'erreur ne se voit pas
en revue. Deux fonctions dont le nom porte l'intention rendent la confusion
visible à la lecture — et permettront d'attacher un privilège de consultation au
seul chemin de lecture, sans qu'aucune écriture ne puisse l'atteindre.

Le passage par la composition root est le même chemin que les vues empruntent
déjà pour obtenir un cas d'usage — il n'ouvre aucune porte nouvelle entre
contextes (voir l'exception documentée dans `.importlinter`).
"""

from __future__ import annotations

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request

from config.container import container
from shared.application.controle_acces import AccesRefuse
from shared.domain.attribution import Capacite
from shared.interface.rest.attribution import auteur_id_de


def exiger_lecture(request: Request, *, bar_id: str, operation: str) -> str:
    """Autorise une consultation, ou lève une 403. Renvoie l'identifiant du lecteur.

    Appartenir au bar suffit : aucune capacité de lecture n'existe dans
    l'énumération, et en inventer une par endpoint donnerait une liste que
    personne ne tiendrait à jour.
    """
    return _exiger(request, bar_id=bar_id, capacite=None, operation=operation)


def exiger_capacite(request: Request, *, bar_id: str, capacite: str, operation: str) -> str:
    """Autorise un acte, ou lève une 403. Renvoie l'identifiant de l'auteur.

    Renvoie l'auteur plutôt que `None` : la vue en a besoin juste après, et le
    lui rendre ici évite un appel séparé qu'on pourrait faire *sans* le garde.
    """
    return _exiger(request, bar_id=bar_id, capacite=capacite, operation=operation)


def exiger_capacite_et_qualite(
    request: Request, *, bar_id: str, capacite: str, operation: str
) -> tuple[str, Capacite]:
    """Autorise l'acte **et** rend la qualité en laquelle l'auteur agit.

    Réservé au seul acte qui inscrit cette qualité au journal — l'ouverture d'un
    service. Le contrôle a déjà chargé le compte pour décider ; la redemander
    ensuite déclenchait une seconde recherche identique, mesurée par
    `tests/test_cout_du_garde.py`.
    """
    auteur = auteur_id_de(request)
    qualite = _autoriser(auteur, bar_id=bar_id, capacite=capacite, operation=operation)
    return auteur, qualite


def _exiger(request: Request, *, bar_id: str, capacite: str | None, operation: str) -> str:
    """Chemin commun. Privé : les vues passent par l'une des deux portes nommées.

    Le message rendu au client reste volontairement muet sur la cause exacte :
    « ce bar n'existe pas » et « il existe mais vous n'y avez pas de compte »
    doivent se ressembler, sinon la réponse devient un moyen d'énumérer les bars
    des autres.
    """
    auteur = auteur_id_de(request)
    _autoriser(auteur, bar_id=bar_id, capacite=capacite, operation=operation)
    return auteur


def _autoriser(auteur_id: str, *, bar_id: str, capacite: str | None, operation: str) -> Capacite:
    """Consulte le port et traduit un refus en 403."""
    try:
        return container.controle_acces().exiger(
            auteur_id=auteur_id,
            bar_id=bar_id,
            capacite=capacite,
            operation=operation,
        )
    except AccesRefuse as refus:
        raise PermissionDenied(str(refus)) from refus


# ---------------------------------------------------------------------------
# Résolution du bar concerné
#
# Séparée de l'autorisation, et non fondue dedans : une fonction par couple
# (objet visé × lecture/écriture) en aurait fait six. Composer deux briques
# nommées se lit mieux, et l'oubli du garde reste impossible — sans lui, la vue
# n'obtient aucun `auteur_id`.
# ---------------------------------------------------------------------------


def bar_du_service(service_id: str) -> str:
    """Le bar d'un service, ou 404.

    Un service **inconnu** reste un 404, conformément au contrat déjà publié.
    Masquer son absence derrière un 403 protégerait d'une énumération, mais les
    identifiants sont des UUID : les parcourir n'est pas une attaque praticable,
    et ce serait payer une réponse trompeuse pour un gain nul. Un service qui
    **existe ailleurs**, lui, donne bien 403 — c'est le garde qui le décide.
    """
    return bar_ou_404(container.bar_du_service(service_id), introuvable="Service introuvable.")


def bar_ou_404(bar_id: str | None, *, introuvable: str) -> str:
    """Transforme un bar non résolu en 404.

    `None` signifie que l'objet visé — produit, client, crédit — n'existe pas.
    """
    if bar_id is None:
        raise NotFound(introuvable)
    return bar_id
