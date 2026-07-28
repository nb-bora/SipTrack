"""Le domaine du catalogue, isolé de toute infrastructure."""

from __future__ import annotations

import pytest

from contexts.catalogue.domain.events import ProduitInscrit, ProduitRetire, TarifModifie
from contexts.catalogue.domain.exceptions import ProduitRetireDeLaVente, TarifInchange
from contexts.catalogue.domain.produit import Produit
from shared.domain.money import Montant


def _produit(prix: int = 1_000) -> Produit:
    return Produit.inscrire(
        bar_id="bar1", nom="33 Export", prix=Montant(prix), auteur_id="gerante1"
    )


def test_un_produit_inscrit_porte_son_prix_et_son_auteur() -> None:
    produit = _produit(1_000)

    assert produit.prix.valeur == 1_000
    assert produit.en_vente is True

    (evenement,) = produit.evenements_non_publies()
    assert isinstance(evenement, ProduitInscrit)
    assert evenement.prix == 1_000
    assert evenement.auteur_id == "gerante1"


def test_le_changement_de_tarif_retient_l_ancien_prix() -> None:
    """Sans l'ancien prix, une recette qui baisse serait indiscernable d'un vol."""
    produit = _produit(1_000)
    produit.purger_evenements()

    produit.changer_le_tarif(nouveau_prix=Montant(1_200), auteur_id="gerante1")

    assert produit.prix.valeur == 1_200
    (evenement,) = produit.evenements_non_publies()
    assert isinstance(evenement, TarifModifie)
    assert evenement.ancien_prix == 1_000
    assert evenement.nouveau_prix == 1_200


def test_reappliquer_le_meme_prix_est_refuse() -> None:
    """Un Fait « le prix passe de 1 000 à 1 000 » ne dit rien."""
    produit = _produit(1_000)

    with pytest.raises(TarifInchange):
        produit.changer_le_tarif(nouveau_prix=Montant(1_000), auteur_id="gerante1")


def test_un_produit_retire_ne_se_vend_plus() -> None:
    produit = _produit()
    produit.purger_evenements()

    produit.retirer_de_la_vente(auteur_id="gerante1")

    assert produit.en_vente is False
    (evenement,) = produit.evenements_non_publies()
    assert isinstance(evenement, ProduitRetire)

    with pytest.raises(ProduitRetireDeLaVente):
        produit.prix_de_vente()


def test_un_produit_en_vente_donne_son_prix() -> None:
    produit = _produit(1_300)

    assert produit.prix_de_vente().valeur == 1_300
