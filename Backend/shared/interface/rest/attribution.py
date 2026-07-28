"""Qui répond du fait que l'on s'apprête à écrire.

Un Fait sans attribution n'existe pas (invariant 2 du modèle métier). Tant que
`auteur_id` venait du corps de la requête, l'attribution était déclarative :
n'importe qui pouvait signer au nom de n'importe qui. Elle est désormais tirée
de la requête authentifiée, et de nulle part ailleurs.

Ce module vit dans `shared/` parce que tout bounded context qui écrit un Fait en
a besoin — le dupliquer par contexte garantirait qu'ils divergent.
"""

from __future__ import annotations

from rest_framework.request import Request


def auteur_id_de(request: Request) -> str:
    """Identifiant stable de l'auteur du fait.

    On journalise la clé technique, jamais le nom d'utilisateur : renommer un
    compte ne doit pas réécrire l'histoire déjà écrite.
    """
    return str(request.user.pk)
