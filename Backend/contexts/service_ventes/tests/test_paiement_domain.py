"""Tests du domaine Paiement — purs, sans Django."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contexts.service_ventes.domain.enums import FormePaiement
from contexts.service_ventes.domain.events import PaiementRecu
from contexts.service_ventes.domain.paiement import Paiement
from shared.domain.money import Montant

_HORODATAGE = datetime(2026, 7, 28, 21, 0, tzinfo=UTC)


def _paiement(montant: int = 1_000) -> Paiement:
    return Paiement.encaisser(
        addition_id="add1",
        service_id="svc1",
        montant=Montant(montant),
        forme_paiement=FormePaiement.ESPECES,
        horodatage=_HORODATAGE,
        auteur_id="u1",
    )


def test_encaisser_emet_l_evenement_paiement_recu() -> None:
    paiement = _paiement(1_300)

    evenements = paiement.evenements_non_publies()
    assert len(evenements) == 1
    evenement = evenements[0]
    assert isinstance(evenement, PaiementRecu)
    assert evenement.paiement_id == paiement.id
    assert evenement.addition_id == "add1"
    assert evenement.montant == 1_300
    assert evenement.forme_paiement == "especes"
    assert evenement.auteur_id == "u1"


def test_un_paiement_nul_est_interdit() -> None:
    with pytest.raises(ValueError):
        _paiement(0)


def test_un_montant_negatif_est_interdit_des_l_objet_valeur() -> None:
    """`Montant` refuse le négatif : un remboursement est un autre Fait."""
    with pytest.raises(ValueError):
        Montant(-100)


def test_purger_les_evenements_vide_la_liste() -> None:
    paiement = _paiement()
    assert len(paiement.evenements_non_publies()) == 1

    paiement.purger_evenements()

    assert paiement.evenements_non_publies() == ()
