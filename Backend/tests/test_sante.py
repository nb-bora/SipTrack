"""L'instance dit ce qu'elle sert, et si elle peut travailler."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_la_sante_est_publique() -> None:
    """Render et la CI l'interrogent sans jeton — c'est sa raison d'être.

    Le dépôt étant public, le commit servi ne révèle rien qu'on ne puisse déjà
    lire sur GitHub.
    """
    reponse = APIClient().get("/api/sante/", format="json")

    assert reponse.status_code == 200


@pytest.mark.django_db
def test_la_sante_annonce_le_commit_servi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans cela, la CI ne peut que supposer avoir déployé.

    C'est exactement ce qui s'est produit sur #56 : hook appelé, pipeline vert,
    et la production servait encore la version précédente.
    """
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234")

    reponse = APIClient().get("/api/sante/", format="json")

    assert reponse.json()["commit"] == "abc1234"


@pytest.mark.django_db
def test_hors_deploiement_le_commit_est_avoue_inconnu() -> None:
    """Mieux vaut « inconnu » qu'une valeur inventée que la CI comparerait."""
    reponse = APIClient().get("/api/sante/", format="json")

    assert reponse.json()["commit"] == "inconnu"


@pytest.mark.django_db
def test_la_sante_eprouve_vraiment_la_base() -> None:
    """Un processus démarré dont la base est morte n'est pas en bonne santé.

    C'est précisément le cas que le contrôle de port de Render laisse passer.
    """
    reponse = APIClient().get("/api/sante/", format="json")

    assert reponse.json()["base"] == "ok"


@pytest.mark.django_db
def test_une_base_injoignable_donne_503() -> None:
    """503 et non 200 : un équilibreur doit pouvoir retirer l'instance."""
    from unittest.mock import patch

    with patch("shared.interface.rest.sante.SanteView._base_repond", return_value=False):
        reponse = APIClient().get("/api/sante/", format="json")

    assert reponse.status_code == 503
    assert reponse.json()["statut"] == "degrade"


@pytest.mark.django_db
def test_la_sante_n_exige_aucune_cle_d_idempotence() -> None:
    """C'est une lecture : l'exiger empêcherait Render de la sonder."""
    reponse = APIClient().get("/api/sante/", format="json")

    assert reponse.status_code == 200
