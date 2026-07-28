"""La documentation de l'API est servie, et elle dit la vérité."""

from __future__ import annotations

from typing import Any

import pytest
import yaml
from rest_framework.test import APIClient


def _schema(client: APIClient) -> dict[str, Any]:
    reponse = client.get("/api/schema/")
    assert reponse.status_code == 200
    schema = yaml.safe_load(reponse.content)
    assert isinstance(schema, dict)
    return schema


@pytest.mark.django_db
def test_le_schema_openapi_est_servi(client_api: APIClient) -> None:
    schema = _schema(client_api)

    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "SipTrack — API"


@pytest.mark.django_db
def test_l_interface_swagger_est_servie(client_api: APIClient) -> None:
    reponse = client_api.get("/api/doc/")

    assert reponse.status_code == 200
    assert b"swagger" in reponse.content.lower()


@pytest.mark.django_db
def test_hors_developpement_la_documentation_reste_fermee() -> None:
    """La carte complète de l'API n'a pas à être publique en production."""
    reponse = APIClient().get("/api/schema/")

    assert reponse.status_code == 401


@pytest.mark.django_db
def test_en_developpement_la_documentation_est_ouverte(settings: Any) -> None:
    """Sinon le navigateur, qui ne porte aucun jeton, afficherait une page vide."""
    settings.DEBUG = True

    reponse = APIClient().get("/api/schema/")

    assert reponse.status_code == 200


@pytest.mark.django_db
def test_le_schema_couvre_toutes_les_routes(client_api: APIClient) -> None:
    """Inventaire exhaustif, volontairement strict.

    Si ce test échoue après l'ajout d'une route, c'est le comportement attendu :
    complétez la liste. Une égalité stricte détecte aussi bien une route non
    documentée qu'une route fantôme laissée par une suppression.
    """
    chemins = set(_schema(client_api)["paths"])

    assert chemins == {
        "/api/auth/jeton/",
        "/api/services/",
        "/api/services/{service_id}/",
        "/api/services/{service_id}/ventes/",
        "/api/services/{service_id}/versement/",
        "/api/services/{service_id}/sous-caisses/",
        "/api/services/{service_id}/cloture/",
        "/api/services/{service_id}/additions/",
        "/api/services/{service_id}/additions/{addition_id}/",
        "/api/services/{service_id}/additions/{addition_id}/paiements/",
        "/api/services/{service_id}/additions/{addition_id}/reglement/",
        "/api/clients/",
        "/api/clients/{client_id}/encours/",
        "/api/bars/{bar_id}/encours/",
        "/api/credits/{credit_id}/remboursements/",
        "/api/produits/",
        "/api/produits/{produit_id}/tarif/",
        "/api/produits/{produit_id}/retrait/",
        "/api/bars/{bar_id}/produits/",
    }


@pytest.mark.django_db
def test_le_schema_ne_documente_aucun_auteur_id_en_entree(client_api: APIClient) -> None:
    """Garde-fou : le jour où quelqu'un remet `auteur_id` dans un corps de requête,
    la documentation le dira — et ce test échouera avant."""
    definitions = _schema(client_api)["components"]["schemas"]

    for nom, definition in definitions.items():
        if nom.endswith("Request"):
            assert "auteur_id" not in definition.get("properties", {}), (
                f"{nom} expose auteur_id : l'auteur doit venir du compte authentifié."
            )
