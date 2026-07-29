"""Rejouer une écriture ne doit produire qu'un seul fait.

L'app mobile est offline-first : à la reconnexion, elle rejoue ce qui n'a pas
abouti. C'est le comportement correct d'un client hors ligne. Sans mémoire des
requêtes déjà traitées, chaque rejeu crée un second fait — et le journal étant
immuable, ce doublon ne se défait pas.

La clé est **obligatoire** sur les écritures. La rendre facultative reviendrait à
compter sur le fait qu'aucun client n'oublie jamais de l'envoyer — or c'est
précisément cet oubli qu'on veut couvrir.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse, JsonResponse

from .models import CLES_CONSERVEES_PAR_DEFAUT, RequeteIdempotente

EN_TETE_CLE = "Idempotency-Key"
EN_TETE_REJEU = "Idempotency-Replayed"

_METHODES_ECRITURE = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Obtenir un jeton n'écrit aucun Fait, et l'exiger là serait circulaire : un
# client sans jeton n'a encore rien à rejouer.
_CHEMINS_EXEMPTES = frozenset({"/api/auth/jeton/"})


class IdempotenceMiddleware:
    """Mémorise chaque écriture, et rend la réponse d'origine à un rejeu."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self._get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self._concerne(request):
            return self._get_response(request)

        cle = request.headers.get(EN_TETE_CLE, "").strip()
        if not cle:
            return self._refus(
                400,
                f"En-tête {EN_TETE_CLE} obligatoire sur les écritures. "
                "Rejouer une requête sans clé créerait un doublon irrécupérable.",
            )

        porteur = self._porteur(request)
        empreinte = self._empreinte(request)

        try:
            # Point de reprise : sans lui, la violation d'unicité — qui est le
            # cas *normal* d'un rejeu, pas une anomalie — condamnerait toute
            # transaction englobante et interdirait la lecture qui suit.
            with transaction.atomic():
                trace = RequeteIdempotente.objects.create(
                    porteur=porteur, cle=cle, empreinte=empreinte
                )
        except IntegrityError:
            return self._repondre_au_rejeu(porteur, cle, empreinte)

        reponse = self._get_response(request)
        self._memoriser(trace, reponse)
        return reponse

    # -- Décisions -------------------------------------------------------

    @staticmethod
    def _concerne(request: HttpRequest) -> bool:
        """Écritures authentifiées sous /api/, hors exemptions.

        Un appel **sans jeton** est laissé passer : il n'a rien à rejouer, et
        c'est à l'authentification de répondre. Lui réclamer une clé
        d'idempotence avant de lui dire qu'il n'est pas identifié inverserait
        l'ordre des refus.
        """
        return (
            request.method in _METHODES_ECRITURE
            and request.path.startswith("/api/")
            and request.path not in _CHEMINS_EXEMPTES
            and bool(request.headers.get("Authorization"))
        )

    @staticmethod
    def _porteur(request: HttpRequest) -> str:
        """Empreinte du jeton, jamais le jeton.

        L'authentification DRF n'a pas encore eu lieu à ce stade : `request.user`
        vaut anonyme même pour un appel authentifié. On se rabat sur l'en-tête,
        qui identifie l'appelant tout aussi bien pour cet usage — et qu'on ne
        conserve que haché.
        """
        return hashlib.sha256(request.headers.get("Authorization", "").encode("utf-8")).hexdigest()

    @staticmethod
    def _empreinte(request: HttpRequest) -> str:
        """Ce que la clé désigne : une méthode, un chemin, un corps."""
        matiere = b"|".join(
            [
                (request.method or "").encode("utf-8"),
                request.path.encode("utf-8"),
                request.body,
            ]
        )
        return hashlib.sha256(matiere).hexdigest()

    # -- Réponses --------------------------------------------------------

    def _repondre_au_rejeu(self, porteur: str, cle: str, empreinte: str) -> HttpResponse:
        trace = RequeteIdempotente.objects.filter(porteur=porteur, cle=cle).first()
        if trace is None:
            # La trace a disparu entre l'échec d'insertion et cette lecture —
            # élagage concurrent. Redemander est la seule réponse honnête.
            return self._refus(409, "Requête concurrente en cours. Réessayez.")

        if trace.empreinte != empreinte:
            return self._refus(
                422,
                f"Cette clé {EN_TETE_CLE} a déjà servi pour une requête différente. "
                "Une clé désigne une écriture précise, pas un appelant.",
            )

        if trace.statut != RequeteIdempotente.TERMINEE:
            # La première requête est encore en vol. Rendre une réponse
            # inventée serait pire que demander de réessayer.
            return self._refus(409, "Requête identique en cours de traitement. Réessayez.")

        reponse = HttpResponse(
            content=bytes(trace.corps or b""),
            status=trace.code_http or 200,
            content_type=trace.type_contenu or "application/json",
        )
        reponse[EN_TETE_REJEU] = "true"
        return reponse

    @staticmethod
    def _refus(code: int, detail: str) -> JsonResponse:
        return JsonResponse({"detail": detail}, status=code)

    # -- Mémorisation ----------------------------------------------------

    def _memoriser(self, trace: RequeteIdempotente, reponse: HttpResponse) -> None:
        """Ne retient que ce qui a abouti.

        Une requête en échec **libère sa clé** : le client doit pouvoir la
        rejouer. Retenir un 500 condamnerait la vente pour de bon, alors que rien
        n'a été écrit — l'Unit of Work a tout annulé.
        """
        if not 200 <= reponse.status_code < 300:
            RequeteIdempotente.objects.filter(pk=trace.pk).delete()
            return

        trace.statut = RequeteIdempotente.TERMINEE
        trace.code_http = reponse.status_code
        trace.corps = reponse.content
        trace.type_contenu = reponse.headers.get("Content-Type", "application/json")
        trace.save(update_fields=["statut", "code_http", "corps", "type_contenu"])
        self._elaguer()

    @staticmethod
    def _elaguer() -> None:
        """Borne la table par la clé primaire, jamais par `COUNT(*)`.

        Compter coûte un parcours ; comparer à la plus grande clé coûte un index.
        """
        plafond = getattr(settings, "IDEMPOTENCE_CLES_MAX", CLES_CONSERVEES_PAR_DEFAUT)
        dernier = RequeteIdempotente.objects.order_by("-id").values_list("id", flat=True).first()
        if dernier is not None and dernier > plafond:
            RequeteIdempotente.objects.filter(id__lt=dernier - plafond).delete()
