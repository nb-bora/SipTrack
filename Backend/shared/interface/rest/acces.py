"""Le garde posé devant chaque acte, à la frontière HTTP.

`attribution.auteur_id_de` dit **qui** écrit. Ce module dit **s'il a le droit** :
il consulte le port `ControleAcces` et traduit un refus en 403.

Une seule fonction, appelée en première ligne de chaque vue qui agit sur un bar.
Elle renvoie l'`auteur_id` plutôt que `None` : la vue en a besoin juste après, et
le lui rendre ici évite un appel séparé qu'on pourrait faire *sans* le garde.

Le passage par la composition root est le même chemin que les vues empruntent
déjà pour obtenir un cas d'usage — il n'ouvre aucune porte nouvelle entre
contextes (voir l'exception documentée dans `.importlinter`).
"""

from __future__ import annotations

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request

from config.container import container
from shared.application.controle_acces import AccesRefuse
from shared.interface.rest.attribution import auteur_id_de


def exiger(request: Request, *, bar_id: str, capacite: str | None, operation: str) -> str:
    """Autorise l'acte, ou lève une 403. Renvoie l'identifiant de l'auteur.

    Le message rendu au client reste volontairement muet sur la cause exacte :
    « ce bar n'existe pas » et « il existe mais vous n'y avez pas de compte »
    doivent se ressembler, sinon la réponse devient un moyen d'énumérer les bars
    des autres.
    """
    auteur = auteur_id_de(request)
    try:
        container.controle_acces().exiger(
            auteur_id=auteur,
            bar_id=bar_id,
            capacite=capacite,
            operation=operation,
        )
    except AccesRefuse as refus:
        raise PermissionDenied(str(refus)) from refus
    return auteur


def exiger_sur_bar_resolu(
    request: Request,
    *,
    bar_id: str | None,
    capacite: str | None,
    operation: str,
    introuvable: str,
) -> str:
    """Garde pour les actes désignés par l'objet visé plutôt que par le bar.

    Le bar est résolu en amont depuis le produit, le client ou le crédit ; il ne
    vient jamais de l'appelant. `bar_id` à `None` signifie que l'objet n'existe
    pas : c'est un 404, pour la même raison que côté service — le contrat le
    publie déjà, et masquer l'absence derrière un 403 ne protégerait que d'une
    énumération d'UUID, qui n'est pas praticable.
    """
    if bar_id is None:
        raise NotFound(introuvable)
    return exiger(request, bar_id=bar_id, capacite=capacite, operation=operation)


def exiger_sur_service(
    request: Request, *, service_id: str, capacite: str | None, operation: str
) -> str:
    """Même garde, pour les actes désignés par un service plutôt qu'un bar.

    La plupart des endpoints de Service & Ventes reçoivent `service_id` dans
    l'URL : le bar concerné se lit sur le service, il n'est jamais fourni par
    l'appelant.

    Un service **inconnu** reste un 404, conformément au contrat déjà publié.
    Masquer son absence derrière un 403 protégerait d'une énumération, mais les
    identifiants sont des UUID : les parcourir n'est pas une attaque praticable,
    et ce serait payer une réponse trompeuse pour un gain nul. Un service qui
    **existe ailleurs**, lui, donne bien 403.
    """
    service = container.service_par_id(service_id)
    if service is None:
        raise NotFound("Service introuvable.")
    return exiger(request, bar_id=service.bar_id, capacite=capacite, operation=operation)
