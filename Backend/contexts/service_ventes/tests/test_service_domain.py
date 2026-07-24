"""Tests du domaine — purs, sans Django (rapides)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contexts.service_ventes.domain.enums import StatutService
from contexts.service_ventes.domain.events import ServiceOuvert
from contexts.service_ventes.domain.service import Service
from shared.domain.attribution import Attribution, Capacite
from shared.domain.money import Montant

_HORODATAGE = datetime(2026, 7, 24, 17, 0, tzinfo=UTC)


def _responsable() -> Attribution:
    return Attribution(auteur_id="u1", capacite=Capacite.OPERATRICE, horodatage=_HORODATAGE)


def test_ouvrir_service_met_le_statut_a_ouvert() -> None:
    service = Service.ouvrir(
        bar_id="bar1",
        responsable=_responsable(),
        fond_de_caisse=Montant(10_000),
        horodatage=_HORODATAGE,
    )

    assert service.statut is StatutService.OUVERT
    assert service.fond_de_caisse == Montant(10_000)
    assert service.bar_id == "bar1"


def test_ouvrir_service_emet_l_evenement_service_ouvert() -> None:
    service = Service.ouvrir(
        bar_id="bar1",
        responsable=_responsable(),
        fond_de_caisse=Montant(10_000),
        horodatage=_HORODATAGE,
    )

    evenements = service.evenements_non_publies()
    assert len(evenements) == 1
    evenement = evenements[0]
    assert isinstance(evenement, ServiceOuvert)
    assert evenement.service_id == service.id
    assert evenement.fond_de_caisse == 10_000


def test_purger_les_evenements_vide_la_liste_des_non_publies() -> None:
    service = Service.ouvrir(
        bar_id="bar1",
        responsable=_responsable(),
        fond_de_caisse=Montant(10_000),
        horodatage=_HORODATAGE,
    )
    assert len(service.evenements_non_publies()) == 1

    service.purger_evenements()

    assert service.evenements_non_publies() == ()


def test_un_montant_negatif_est_interdit() -> None:
    with pytest.raises(ValueError):
        Montant(-1)


def test_addition_de_deux_montants_de_meme_devise() -> None:
    assert Montant(100) + Montant(50) == Montant(150)


def test_soustraction_de_deux_montants_de_meme_devise() -> None:
    assert Montant(200) - Montant(75) == Montant(125)


def test_operer_sur_des_devises_differentes_est_interdit() -> None:
    xaf = Montant(100, "XAF")
    eur = Montant(50, "EUR")

    with pytest.raises(ValueError):
        _ = xaf + eur

    with pytest.raises(ValueError):
        _ = xaf - eur
