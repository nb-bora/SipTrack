"""Tests du domaine Vente — purs, sans Django."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contexts.service_ventes.domain.enums import FormePaiement
from contexts.service_ventes.domain.events import VenteEnregistree
from contexts.service_ventes.domain.vente import Vente
from shared.domain.money import Montant

_HORODATAGE = datetime(2026, 7, 24, 18, 30, tzinfo=UTC)


def _vente(quantite: int = 3, addition_id: str | None = None) -> Vente:
    return Vente.enregistrer(
        service_id="svc1",
        produit_id="33export",
        quantite=quantite,
        prix_unitaire=Montant(650),
        forme_paiement=FormePaiement.ESPECES,
        horodatage=_HORODATAGE,
        auteur_id="u1",
        addition_id=addition_id,
    )


def test_enregistrer_une_vente_calcule_le_montant_total() -> None:
    assert _vente(quantite=3).montant_total == Montant(1_950)


def test_enregistrer_une_vente_emet_l_evenement() -> None:
    vente = _vente(quantite=2)

    evenements = vente.evenements_non_publies()
    assert len(evenements) == 1
    evenement = evenements[0]
    assert isinstance(evenement, VenteEnregistree)
    assert evenement.vente_id == vente.id
    assert evenement.montant_total == 1_300
    assert evenement.forme_paiement == "especes"


@pytest.mark.parametrize("quantite", [0, -1])
def test_une_quantite_nulle_ou_negative_est_interdite(quantite: int) -> None:
    with pytest.raises(ValueError):
        _vente(quantite=quantite)


def test_une_vente_peut_porter_une_addition() -> None:
    vente = _vente(addition_id="add1")

    assert vente.addition_id == "add1"
    evenement = vente.evenements_non_publies()[0]
    assert isinstance(evenement, VenteEnregistree)
    assert evenement.addition_id == "add1"


def test_une_vente_au_comptoir_ne_porte_aucune_addition() -> None:
    vente = _vente()

    assert vente.addition_id is None
    evenement = vente.evenements_non_publies()[0]
    assert isinstance(evenement, VenteEnregistree)
    assert evenement.addition_id is None
