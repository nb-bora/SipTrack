"""Implémentation Django du côté lecture (CQRS).

Contrairement aux repositories, le query service **ne reconstruit pas
d'agrégats** : il lit les tables et produit directement les DTO de lecture. Le
total est agrégé ici, à partir des lignes — il n'est stocké nulle part.
"""

from __future__ import annotations

from contexts.service_ventes.application.queries import AdditionDetailDTO, LigneAdditionDTO
from contexts.service_ventes.infrastructure.django_app.models import AdditionModel, VenteModel


class DjangoAdditionQueryService:
    def detail(self, *, service_id: str, addition_id: str) -> AdditionDetailDTO | None:
        try:
            addition = AdditionModel.objects.get(pk=addition_id, service_id=service_id)
        except AdditionModel.DoesNotExist:
            return None

        lignes = tuple(
            LigneAdditionDTO(
                vente_id=vente.id,
                produit_id=vente.produit_id,
                quantite=vente.quantite,
                prix_unitaire=vente.prix_unitaire,
                montant_total=vente.montant_total,
                forme_paiement=vente.forme_paiement,
                horodatage=vente.horodatage.isoformat(),
            )
            for vente in VenteModel.objects.filter(addition_id=addition_id).order_by("horodatage")
        )

        return AdditionDetailDTO(
            id=addition.id,
            service_id=addition.service_id,
            table_numero=addition.table_numero,
            statut=addition.statut,
            ouvert_le=addition.ouvert_le.isoformat(),
            ferme_le=addition.ferme_le.isoformat() if addition.ferme_le is not None else None,
            lignes=lignes,
            total=sum(ligne.montant_total for ligne in lignes),
        )
