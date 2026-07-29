"""Ce que sert réellement l'instance, et si elle tient debout.

Render se contente de vérifier qu'un port répond. Un processus démarré dont la
base est injoignable passe donc pour vivant, et le déploiement se déclare réussi
alors que l'API renvoie des 500.

Ce point d'entrée répond à deux questions qu'on ne pouvait pas poser :

- **quel commit est servi ?** — sans quoi la CI ne peut pas constater qu'elle a
  déployé, seulement espérer l'avoir fait ;
- **la base répond-elle ?** — la seule dépendance sans laquelle rien ne marche.

Publique, et le dépôt l'est aussi : le commit ne révèle rien qu'on ne puisse
lire sur GitHub. C'est ce qui lève l'objection qui avait justifié son absence
(cf. `docs/06-deploiement.md`).
"""

from __future__ import annotations

import os

from django.db import connection
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

# Render la pose sur chaque instance. Vide en local : on ne prétend pas
# connaître un commit qu'on ne sert pas depuis un déploiement.
_VARIABLE_COMMIT = "RENDER_GIT_COMMIT"


class SanteSerializer(serializers.Serializer[dict[str, object]]):
    statut = serializers.CharField()
    commit = serializers.CharField()
    base = serializers.CharField()


class SanteView(APIView):
    """Vivant *et* capable de travailler — les deux, ou rien."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Exploitation"],
        summary="État de l'instance",
        description=(
            "Rend le commit servi et l'état de la base. Sert au déploiement "
            "continu, qui attend d'y lire le commit attendu avant de se déclarer "
            "réussi."
        ),
        responses={
            200: SanteSerializer,
            503: OpenApiResponse(
                response=SanteSerializer,
                description="La base ne répond pas : l'instance est démarrée mais inapte.",
            ),
        },
    )
    def get(self, request: Request) -> Response:
        base_accessible = self._base_repond()
        charge = {
            "statut": "ok" if base_accessible else "degrade",
            "commit": os.environ.get(_VARIABLE_COMMIT, "inconnu"),
            "base": "ok" if base_accessible else "injoignable",
        }
        return Response(
            charge,
            status=status.HTTP_200_OK if base_accessible else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @staticmethod
    def _base_repond() -> bool:
        """Une requête réelle, pas un simple `connection is not None`.

        Django garde des connexions ouvertes : tester l'objet dirait « oui »
        alors que le serveur est tombé. Seul un aller-retour le prouve.
        """
        try:
            with connection.cursor() as curseur:
                curseur.execute("SELECT 1")
                return curseur.fetchone() is not None
        except Exception:  # noqa: BLE001 — toute panne de base vaut « injoignable ».
            return False
