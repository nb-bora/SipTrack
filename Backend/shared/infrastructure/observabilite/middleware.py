"""Ce qui s'est passé sur chaque requête, sans ce qu'elle contenait.

Trois choses, et trois seulement :

- un identifiant de corrélation, rendu dans l'en-tête, qui relie une plainte
  d'utilisateur aux lignes de log correspondantes ;
- une ligne par requête : méthode, chemin, statut, durée, auteur ;
- les 5xx conservés en base, avec leur trace.

**Jamais les corps.** Ils portent des noms de clients, des dettes, des montants.
En garder une copie créerait un second exemplaire des données sensibles, moins
bien protégé que l'original.
"""

from __future__ import annotations

import logging
import time
import traceback
from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from shared.domain.identifiers import new_id

from .models import LIGNES_CONSERVEES_PAR_DEFAUT, ErreurTechnique

_logger = logging.getLogger("siptrack.requete")

EN_TETE_CORRELATION = "X-Correlation-Id"

# Au-delà, la requête mérite d'être regardée. Le plan Render gratuit met le
# service en veille : le premier appel après un réveil dépasse largement ce
# seuil, et c'est normal — d'où `reveil` plutôt que `lent` dans ce cas.
SEUIL_LENTEUR_MS = 1_000
SEUIL_REVEIL_MS = 10_000


class ObservabiliteMiddleware:
    """Mesure, journalise, et n'interrompt jamais la requête qu'il observe."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self._get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.headers.get(EN_TETE_CORRELATION) or new_id()
        request.correlation_id = correlation_id  # type: ignore[attr-defined]
        debut = time.perf_counter()

        reponse = self._get_response(request)

        duree_ms = round((time.perf_counter() - debut) * 1000, 1)
        reponse[EN_TETE_CORRELATION] = correlation_id

        contexte = {
            "correlation_id": correlation_id,
            "methode": request.method,
            "chemin": request.path,
            "statut": reponse.status_code,
            "duree_ms": duree_ms,
            "auteur_id": self._auteur(request),
        }
        _logger.log(self._niveau(reponse.status_code, duree_ms), "requete", extra=contexte)

        if reponse.status_code >= 500:
            self._conserver(request, reponse, correlation_id)
        return reponse

    @staticmethod
    def _auteur(request: HttpRequest) -> str:
        """L'identifiant technique, jamais le nom d'utilisateur.

        Renommer un compte ne doit pas rendre illisibles les logs déjà écrits —
        même raison que dans le journal métier.
        """
        utilisateur = getattr(request, "user", None)
        if utilisateur is None or not utilisateur.is_authenticated:
            return ""
        return str(utilisateur.pk)

    @staticmethod
    def _niveau(statut: int, duree_ms: float) -> int:
        if statut >= 500:
            return logging.ERROR
        if SEUIL_LENTEUR_MS <= duree_ms < SEUIL_REVEIL_MS:
            return logging.WARNING
        return logging.INFO

    def _conserver(self, request: HttpRequest, reponse: HttpResponse, correlation_id: str) -> None:
        """Garde la panne en base, sans jamais aggraver l'incident.

        Si la base est ce qui est cassé, cette écriture échoue aussi : elle ne
        doit pas transformer une erreur en deux.
        """
        try:
            ErreurTechnique.objects.create(
                correlation_id=correlation_id,
                methode=request.method or "",
                chemin=request.path[:255],
                statut=reponse.status_code,
                auteur_id=self._auteur(request),
                exception=self._exception_courante(),
                trace=traceback.format_exc(limit=30) if self._exception_courante() else "",
            )
            self._elaguer()
        except Exception:  # noqa: BLE001 — voir la docstring.
            _logger.exception(
                "Erreur technique non conservee", extra={"correlation_id": correlation_id}
            )

    @staticmethod
    def _exception_courante() -> str:
        import sys

        exception = sys.exc_info()[1]
        return "" if exception is None else f"{type(exception).__name__}: {exception}"[:255]

    @staticmethod
    def _elaguer() -> None:
        """Borne la table par la clé primaire, sans jamais compter les lignes.

        `COUNT(*)` coûte un parcours ; comparer au plus grand identifiant coûte
        un index. La différence compte précisément quand elle sert : pendant une
        boucle d'erreurs.
        """
        plafond = getattr(settings, "OBSERVABILITE_ERREURS_MAX", LIGNES_CONSERVEES_PAR_DEFAUT)
        dernier = ErreurTechnique.objects.order_by("-id").values_list("id", flat=True).first()
        if dernier is not None and dernier > plafond:
            ErreurTechnique.objects.filter(id__lt=dernier - plafond).delete()
