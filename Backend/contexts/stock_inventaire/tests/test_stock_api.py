"""Tests d'intégration de l'API Stock & Inventaire."""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_creer_produit(client_api: APIClient, auteur: Any) -> None:
    """Créer un produit dans un bar."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    reponse = client_api.post(
        "/api/inventaire/produits/",
        {
            "bar_id": bar["id"],
            "nom": "Bière 33cl",
            "quantite_initiale": 50,
        },
        format="json",
    )

    if reponse.status_code != 201:
        print(f"Error response: {reponse.json()}")
    assert reponse.status_code == 201
    assert reponse.json()["nom"] == "Bière 33cl"
    assert reponse.json()["quantite"] == 50


@pytest.mark.django_db
def test_lister_produits(client_api: APIClient, auteur: Any) -> None:
    """Lister les produits d'un bar."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    client_api.post(
        "/api/inventaire/produits/",
        {"bar_id": bar["id"], "nom": "Bière", "quantite_initiale": 50},
        format="json",
    )
    client_api.post(
        "/api/inventaire/produits/",
        {"bar_id": bar["id"], "nom": "Vin", "quantite_initiale": 30},
        format="json",
    )

    reponse = client_api.get(f"/api/inventaire/produits/?bar_id={bar['id']}", format="json")

    assert reponse.status_code == 200
    assert len(reponse.json()) == 2


@pytest.mark.django_db
def test_ajouter_stock(client_api: APIClient, auteur: Any) -> None:
    """Ajouter du stock à un produit."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    produit = client_api.post(
        "/api/inventaire/produits/",
        {"bar_id": bar["id"], "nom": "Bière", "quantite_initiale": 50},
        format="json",
    ).json()

    reponse = client_api.post(
        f"/api/inventaire/produits/{produit['id']}/stock/",
        {"quantite": 20},
        format="json",
    )

    assert reponse.status_code == 200
    assert reponse.json()["quantite"] == 70


@pytest.mark.django_db
def test_vendre_produit(client_api: APIClient, auteur: Any) -> None:
    """Enregistrer une vente."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    produit = client_api.post(
        "/api/inventaire/produits/",
        {"bar_id": bar["id"], "nom": "Bière", "quantite_initiale": 50},
        format="json",
    ).json()

    reponse = client_api.post(
        f"/api/inventaire/produits/{produit['id']}/vendre/",
        {"quantite": 10},
        format="json",
    )

    assert reponse.status_code == 200
    assert reponse.json()["quantite"] == 40


@pytest.mark.django_db
def test_vendre_plus_que_stock(client_api: APIClient, auteur: Any) -> None:
    """Vendre plus que le stock disponible est refusé."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    produit = client_api.post(
        "/api/inventaire/produits/",
        {"bar_id": bar["id"], "nom": "Bière", "quantite_initiale": 50},
        format="json",
    ).json()

    reponse = client_api.post(
        f"/api/inventaire/produits/{produit['id']}/vendre/",
        {"quantite": 60},
        format="json",
    )

    assert reponse.status_code == 409


@pytest.mark.django_db
def test_corriger_inventaire(client_api: APIClient, auteur: Any) -> None:
    """Corriger l'inventaire."""
    bar = client_api.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    produit = client_api.post(
        "/api/inventaire/produits/",
        {"bar_id": bar["id"], "nom": "Bière", "quantite_initiale": 50},
        format="json",
    ).json()

    reponse = client_api.put(
        f"/api/inventaire/produits/{produit['id']}/inventaire/",
        {"quantite_nouvelle": 48, "raison": "Casse lors du transport"},
        format="json",
    )

    assert reponse.status_code == 200
    assert reponse.json()["quantite"] == 48
