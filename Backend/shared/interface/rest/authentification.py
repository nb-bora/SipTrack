"""Un jeton ne vaut pas pour toujours, et doit pouvoir être rendu.

`TokenAuthentication` de DRF délivre un jeton **opaque et permanent** : il
n'expire jamais et ne se révoque qu'en le supprimant en base. Pour l'usage visé
— des téléphones qui circulent dans un bar, qui se perdent, qui se volent — cela
revient à donner un trousseau de clés qu'on ne peut pas reprendre.

Deux ajouts, et rien de plus :

- une **durée de vie**, au-delà de laquelle le jeton n'ouvre plus rien ;
- une **révocation** explicite, pour rendre ses clés avant l'échéance.

Le format du jeton ne change pas : les clients existants continuent de
fonctionner jusqu'à expiration.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


class JetonExpirable(TokenAuthentication):
    """Refuse un jeton trop ancien, et le supprime au passage.

    Le supprimer plutôt que le laisser dormir évite qu'une table de jetons morts
    grossisse indéfiniment, et rend le refus définitif : un jeton expiré ne
    redevient pas valide si l'horloge recule.
    """

    def authenticate_credentials(self, key: str) -> tuple[object, Token]:
        utilisateur, jeton = super().authenticate_credentials(key)

        if self._est_perime(jeton):
            jeton.delete()
            raise AuthenticationFailed("Jeton expiré. Reconnectez-vous.")

        return utilisateur, jeton

    @staticmethod
    def _est_perime(jeton: Token) -> bool:
        duree = timedelta(days=settings.JETON_DUREE_JOURS)
        return bool(timezone.now() - jeton.created > duree)
