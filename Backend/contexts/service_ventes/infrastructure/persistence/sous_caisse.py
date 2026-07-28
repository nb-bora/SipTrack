"""Lecture des sous-caisses d'un service (CQRS).

La vue quotidienne de la gérante : pour chaque personne ayant encaissé, ce
qu'elle doit rapporter et ce qu'elle a remis.

Les serveuses sont **déduites des encaissements**, pas d'une liste d'équipe :
le contexte ne connaît pas encore l'affectation du personnel, et quiconque a
encaissé doit rendre des comptes — y compris la gérante elle-même.
"""

from __future__ import annotations

from django.db.models import Sum

from contexts.service_ventes.application.queries import SousCaisseDTO
from contexts.service_ventes.domain.enums import FormePaiement
from contexts.service_ventes.infrastructure.django_app.models import (
    PaiementModel,
    VersementModel,
)


class DjangoSousCaisseQueryService:
    def par_service(self, service_id: str) -> tuple[SousCaisseDTO, ...]:
        encaissements = (
            PaiementModel.objects.filter(service_id=service_id)
            .values("auteur_id", "forme_paiement")
            .annotate(somme=Sum("montant"))
        )

        par_auteur: dict[str, dict[str, int]] = {}
        for ligne in encaissements:
            compteurs = par_auteur.setdefault(ligne["auteur_id"], {"especes": 0, "mobile_money": 0})
            if ligne["forme_paiement"] == FormePaiement.ESPECES.value:
                compteurs["especes"] += int(ligne["somme"] or 0)
            elif ligne["forme_paiement"] == FormePaiement.MOBILE_MONEY.value:
                compteurs["mobile_money"] += int(ligne["somme"] or 0)

        versements = {
            versement.serveuse_id: versement
            for versement in VersementModel.objects.filter(service_id=service_id)
        }
        # Une serveuse ayant versé sans rien encaisser doit rester visible :
        # c'est un écart, pas une ligne à masquer.
        for serveuse_id in versements:
            par_auteur.setdefault(serveuse_id, {"especes": 0, "mobile_money": 0})

        return tuple(
            SousCaisseDTO(
                serveuse_id=serveuse_id,
                encaisse_especes=compteurs["especes"],
                encaisse_mobile_money=compteurs["mobile_money"],
                verse=versements[serveuse_id].verse if serveuse_id in versements else None,
                ecart=versements[serveuse_id].ecart if serveuse_id in versements else None,
            )
            for serveuse_id, compteurs in sorted(par_auteur.items())
        )
