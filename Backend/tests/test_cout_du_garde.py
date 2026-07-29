"""Le garde ne doit pas coûter plus qu'il ne faut.

Une affirmation de performance qui n'est pas mesurée cesse d'être vraie à la
première refonte. Ces bornes ne visent pas la finesse : elles visent le retour
silencieux de la lecture en double.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_le_garde_ne_recharge_pas_l_objet_entier(client_api: APIClient, bar_de_test: str) -> None:
    """Résoudre le bar d'un service ne ramène qu'une colonne, par clé primaire.

    Le garde a besoin de `bar_id`, rien d'autre ; le cas d'usage rechargera le
    service de toute façon. Reconstruire l'agrégat deux fois se paierait sur
    chaque requête portée par un service — la majorité de l'API.
    """
    service_id = client_api.post(
        "/api/services/",
        {"bar_id": bar_de_test, "fond_de_caisse": 10_000},
        format="json",
    ).json()["id"]

    with CaptureQueriesContext(connection) as requetes:
        reponse = client_api.get(f"/api/services/{service_id}/", format="json")

    assert reponse.status_code == 200
    resolutions = [
        r["sql"]
        for r in requetes.captured_queries
        if "service_ventes_service" in r["sql"]
        and 'SELECT "service_ventes_service"."bar_id"' in r["sql"]
    ]
    assert len(resolutions) == 1, (
        f"La résolution du bar devrait tirer une seule colonne, une seule fois. "
        f"Requêtes vues : {[r['sql'] for r in requetes.captured_queries]}"
    )


@pytest.mark.django_db
def test_un_compte_ordinaire_ne_paie_qu_une_recherche_de_droits(
    client_api: APIClient, bar_de_test: str
) -> None:
    """Le chemin courant reste à une seule recherche de compte.

    Elle s'appuie sur la contrainte d'unicité `(bar, user)`, donc sur un index.
    Cette borne existe pour qu'un privilège ajouté plus tard ne s'installe pas
    en travers du chemin de tout le monde.
    """
    with CaptureQueriesContext(connection) as requetes:
        reponse = client_api.post(
            "/api/services/",
            {"bar_id": bar_de_test, "fond_de_caisse": 10_000},
            format="json",
        )

    assert reponse.status_code == 201
    recherches: list[Any] = [
        r["sql"] for r in requetes.captured_queries if "gouvernance_compte" in r["sql"]
    ]
    assert len(recherches) == 1, f"{len(recherches)} recherches de compte : {recherches}"
