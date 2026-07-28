"""Tests du domaine Versement — purs, sans Django."""

from __future__ import annotations

from datetime import UTC, datetime

from contexts.service_ventes.domain.events import EcartConstate, RecetteVersee
from contexts.service_ventes.domain.versement import Versement
from shared.domain.money import Montant

_HORODATAGE = datetime(2026, 7, 28, 23, 0, tzinfo=UTC)


def _versement(attendu: int, verse: int) -> Versement:
    return Versement.remettre(
        service_id="svc1",
        serveuse_id="serveuse1",
        attendu=Montant(attendu),
        verse=Montant(verse),
        horodatage=_HORODATAGE,
    )


def test_une_recette_juste_n_emet_que_le_versement() -> None:
    versement = _versement(2_000, 2_000)

    assert versement.ecart == 0
    evenements = versement.evenements_non_publies()
    assert len(evenements) == 1
    assert isinstance(evenements[0], RecetteVersee)


def test_un_manquant_emet_aussi_un_ecart() -> None:
    versement = _versement(2_000, 1_500)

    assert versement.ecart == -500
    evenements = versement.evenements_non_publies()
    assert [type(e) for e in evenements] == [RecetteVersee, EcartConstate]
    ecart = evenements[1]
    assert isinstance(ecart, EcartConstate)
    assert ecart.ecart == -500


def test_un_excedent_emet_aussi_un_ecart() -> None:
    """Un excédent est tout aussi inexpliqué qu'un manquant."""
    versement = _versement(1_000, 1_200)

    assert versement.ecart == 200
    assert len(versement.evenements_non_publies()) == 2


def test_un_ecart_d_un_franc_est_constate() -> None:
    """« Zéro inexpliqué » : aucun seuil de tolérance (invariant 4)."""
    versement = _versement(1_000, 999)

    assert versement.ecart == -1
    assert len(versement.evenements_non_publies()) == 2


def test_une_serveuse_qui_n_a_rien_encaisse_et_ne_verse_rien_est_a_l_equilibre() -> None:
    versement = _versement(0, 0)

    assert versement.ecart == 0
    assert len(versement.evenements_non_publies()) == 1
