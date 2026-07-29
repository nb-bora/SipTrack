"""Ce qu'un compte affirme de lui-même ne lui donne aucun droit.

Deux questions distinctes, souvent confondues :

- **Où** ai-je le droit d'agir ? — le cloisonnement entre bars.
- **Quoi** ai-je le droit de faire ? — les capacités accordées.

Tant que `bar_id` et `capacite` arrivaient dans le corps de la requête, les deux
réponses venaient de l'appelant. C'est la même faille que `auteur_id` : une
déclaration n'est pas une preuve.

Ces tests passent par HTTP uniquement — aucun import d'un contexte, donc aucune
entorse au contrat d'isolation (ADR-0005).
"""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient


def _client_de(utilisateur: Any) -> APIClient:
    """Un client REST authentifié au nom de cet utilisateur."""
    from rest_framework.authtoken.models import Token

    from conftest import ClientAvecCleIdempotente

    jeton, _ = Token.objects.get_or_create(user=utilisateur)
    client = ClientAvecCleIdempotente()
    client.credentials(HTTP_AUTHORIZATION=f"Token {jeton.key}")
    return client


@pytest.fixture
def patronne(db: None, django_user_model: Any) -> Any:
    """Propriétaire du bar où l'on a le droit d'être."""
    return django_user_model.objects.create_user(username="patronne")


@pytest.fixture
def voisin(db: None, django_user_model: Any) -> Any:
    """Propriétaire d'un autre bar, qui ne nous a rien demandé."""
    return django_user_model.objects.create_user(username="voisin")


@pytest.fixture
def bar_du_voisin(voisin: Any) -> str:
    """Un bar dont nous ne sommes ni propriétaire ni employé."""
    reponse = _client_de(voisin).post("/api/bars/", {"nom": "Chez le voisin"}, format="json")
    assert reponse.status_code == 201
    identifiant = reponse.json()["id"]
    assert isinstance(identifiant, str)
    return identifiant


# ---------------------------------------------------------------------------
# Cloisonnement : où ai-je le droit d'agir ?
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ouvrir_un_service_chez_le_voisin_est_refuse(patronne: Any, bar_du_voisin: str) -> None:
    """Le cas qui rend l'outil inutilisable s'il passe.

    Un bar est un lieu de confiance fermé. Que la patronne d'un bar puisse
    ouvrir un service chez son concurrent vide le produit de son sens.
    """
    reponse = _client_de(patronne).post(
        "/api/services/",
        {"bar_id": bar_du_voisin, "capacite": "operatrice", "fond_de_caisse": 50_000},
        format="json",
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_inscrire_un_produit_chez_le_voisin_est_refuse(patronne: Any, bar_du_voisin: str) -> None:
    """Le cloisonnement ne vaut que s'il tient sur *tous* les contextes.

    Un seul endpoint oublié suffit à rouvrir la porte : ce test existe pour que
    l'ajout d'un contexte sans contrôle se voie.
    """
    reponse = _client_de(patronne).post(
        "/api/produits/",
        {"bar_id": bar_du_voisin, "nom": "Biere", "prix": 1000},
        format="json",
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_creer_un_client_chez_le_voisin_est_refuse(patronne: Any, bar_du_voisin: str) -> None:
    """Les créances d'un bar sont ses affaires, pas celles du voisin."""
    reponse = _client_de(patronne).post(
        "/api/clients/",
        {"bar_id": bar_du_voisin, "nom": "Client fantome"},
        format="json",
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_creer_du_stock_chez_le_voisin_est_refuse(patronne: Any, bar_du_voisin: str) -> None:
    """Écrire dans l'inventaire d'autrui fausse ses comptes, pas les nôtres."""
    reponse = _client_de(patronne).post(
        "/api/inventaire/produits/",
        {"bar_id": bar_du_voisin, "nom": "Casier", "quantite_initiale": 10},
        format="json",
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_lire_les_encours_du_voisin_est_refuse(patronne: Any, bar_du_voisin: str) -> None:
    """La lecture compte autant que l'écriture.

    Connaître qui doit combien chez le concurrent est déjà une fuite, même sans
    rien modifier.
    """
    reponse = _client_de(patronne).get(f"/api/bars/{bar_du_voisin}/encours/", format="json")

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_chez_soi_reste_permis(patronne: Any) -> None:
    """Le garde-fou doit refuser l'intrusion sans gêner le travail.

    Sans ce test, tout refuser ferait passer les précédents.
    """
    bar = _client_de(patronne).post("/api/bars/", {"nom": "Chez moi"}, format="json").json()

    reponse = _client_de(patronne).post(
        "/api/services/",
        {"bar_id": bar["id"], "capacite": "operatrice", "fond_de_caisse": 50_000},
        format="json",
    )

    assert reponse.status_code == 201


# ---------------------------------------------------------------------------
# Capacités : quoi ai-je le droit de faire ?
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_agir_sans_la_capacite_est_refuse(patronne: Any, django_user_model: Any) -> None:
    """Une serveuse embauchée pour saisir des ventes ne clôture pas la caisse.

    Clôturer arrête les compteurs de la soirée. C'est l'acte qui fige les
    écarts : le confier à qui n'en répond pas retire tout sens à la
    réconciliation.
    """
    client_patronne = _client_de(patronne)
    bar = client_patronne.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    # Une serveuse qui ne sait qu'enregistrer des ventes.
    serveuse = django_user_model.objects.create_user(username="serveuse")
    client_patronne.post(
        "/api/comptes/",
        {
            "bar_id": bar["id"],
            "user_id": str(serveuse.pk),
            "capacites_initiales": ["enregistrer_vente"],
        },
        format="json",
    )

    service = client_patronne.post(
        "/api/services/",
        {"bar_id": bar["id"], "capacite": "operatrice", "fond_de_caisse": 50_000},
        format="json",
    ).json()

    reponse = _client_de(serveuse).post(
        f"/api/services/{service['id']}/cloture/", {}, format="json"
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_la_capacite_ne_se_declare_pas_dans_la_requete(
    patronne: Any, django_user_model: Any
) -> None:
    """Le cœur de la faille : s'attribuer un droit en le nommant.

    Même en réclamant explicitement la capacité manquante, la réponse ne change
    pas. Sinon le contrôle ne serait qu'une formalité contournable par un champ.
    """
    client_patronne = _client_de(patronne)
    bar = client_patronne.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    serveuse = django_user_model.objects.create_user(username="serveuse2")
    client_patronne.post(
        "/api/comptes/",
        {
            "bar_id": bar["id"],
            "user_id": str(serveuse.pk),
            "capacites_initiales": ["enregistrer_vente"],
        },
        format="json",
    )

    service = client_patronne.post(
        "/api/services/",
        {"bar_id": bar["id"], "capacite": "operatrice", "fond_de_caisse": 50_000},
        format="json",
    ).json()

    reponse = _client_de(serveuse).post(
        f"/api/services/{service['id']}/cloture/",
        {"capacite": "cloturer_service"},
        format="json",
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_avec_la_capacite_l_acte_passe(patronne: Any, django_user_model: Any) -> None:
    """La contrepartie : accorder la capacité doit suffire à débloquer l'acte."""
    client_patronne = _client_de(patronne)
    bar = client_patronne.post("/api/bars/", {"nom": "Le Relais"}, format="json").json()

    gerante = django_user_model.objects.create_user(username="gerante")
    client_patronne.post(
        "/api/comptes/",
        {
            "bar_id": bar["id"],
            "user_id": str(gerante.pk),
            "capacites_initiales": ["ouvrir_service", "cloturer_service"],
        },
        format="json",
    )

    service = _client_de(gerante).post(
        "/api/services/",
        {"bar_id": bar["id"], "capacite": "operatrice", "fond_de_caisse": 50_000},
        format="json",
    )

    assert service.status_code == 201


# ---------------------------------------------------------------------------
# Garde-fous durables
# ---------------------------------------------------------------------------


def test_le_vocabulaire_des_capacites_ne_peut_pas_diverger() -> None:
    """`CapaciteRequise` est le miroir de `CapaciteAtomique` — à l'identique.

    Le miroir existe pour qu'une vue nomme ce qu'elle exige sans importer
    Gouvernance (ADR-0005). Sans ce test, ajouter une capacité d'un seul côté
    passerait inaperçu jusqu'au jour où un endpoint exigerait une capacité que
    personne ne peut détenir — donc un refus permanent, ou pire, une faute de
    frappe qui n'exige plus rien.
    """
    from contexts.gouvernance_acces.domain.enums import CapaciteAtomique
    from shared.application.controle_acces import CapaciteRequise

    assert {c.value for c in CapaciteRequise} == CapaciteAtomique.toutes()


@pytest.mark.django_db
def test_aucun_endpoint_ne_repond_a_un_inconnu(django_user_model: Any) -> None:
    """Une personne authentifiée mais sans aucun compte n'obtient rien, nulle part.

    Ce test énumère les routes réellement déclarées, plutôt que d'en tenir une
    liste à la main. C'est ce qui le rend utile : le jour où un contexte
    supplémentaire arrive avec un endpoint non gardé, il échoue ici — sans que
    personne ait eu à y penser.

    Un inconnu peut légitimement recevoir 401, 403, 404, 400 ou 405. Ce qu'il ne
    doit jamais recevoir, c'est un succès.
    """
    from django.urls import get_resolver

    inconnu = django_user_model.objects.create_user(username="inconnu-total")
    client = _client_de(inconnu)

    hors_perimetre = {
        # Délivre le jeton : exiger un compte pour l'obtenir serait circulaire.
        "/api/auth/jeton/",
        # Documentation publique, volontairement ouverte.
        "/api/schema/",
        # État de l'instance : Render la sonde et la CI l'interroge pour
        # constater qu'un déploiement a bien abouti. Ni l'un ni l'autre ne
        # porte de jeton. Elle ne rend que le commit servi — que le dépôt
        # étant public, n'importe qui peut déjà lire — et l'état de la base.
        "/api/sante/",
        "/api/doc/",
        "/api/redoc/",
        # Créer son premier bar et lister les siens : le seul point d'entrée de
        # quelqu'un qui n'a encore de compte nulle part. La réponse est bornée à
        # l'appelant — `test_lister_les_bars_ne_montre_que_les_siens` le prouve.
        "/api/bars/",
    }

    testees = 0
    for motif in get_resolver().url_patterns:
        for chemin in _chemins_de(motif, prefixe=""):
            # L'admin Django a son propre contrôle d'accès, hors du périmètre
            # des capacités métier.
            if not chemin.startswith("/api/") or chemin in hors_perimetre:
                continue
            for methode in ("get", "post"):
                reponse = getattr(client, methode)(chemin, {}, format="json")
                assert not str(reponse.status_code).startswith("2"), (
                    f"{methode.upper()} {chemin} répond {reponse.status_code} "
                    f"à un compte qui n'existe dans aucun bar."
                )
                testees += 1

    # Sans cette borne, une énumération qui ne trouverait rien ferait passer le
    # test en silence — le pire des faux verts.
    assert testees > 20, f"Seules {testees} routes éprouvées : l'énumération a échoué."


def _chemins_de(motif: Any, *, prefixe: str) -> list[str]:
    """Aplatit l'arbre des URLs en chemins concrets, paramètres substitués."""
    import re

    from django.urls import URLPattern, URLResolver

    brut = prefixe + str(motif.pattern)
    if isinstance(motif, URLResolver):
        chemins: list[str] = []
        for enfant in motif.url_patterns:
            chemins.extend(_chemins_de(enfant, prefixe=brut))
        return chemins
    if not isinstance(motif, URLPattern):
        return []

    # `<str:service_id>` → un identifiant qui n'existe pas : ce qui compte est
    # le refus, et il doit tomber avant toute recherche en base.
    concret = re.sub(r"<[^>]+>", "inexistant", brut)
    if "(?P<" in concret or "\\" in concret:
        return []
    return ["/" + concret.lstrip("/")]


@pytest.mark.django_db
def test_lister_les_bars_ne_montre_que_les_siens(patronne: Any, bar_du_voisin: str) -> None:
    """La seule route ouverte à qui n'a de compte nulle part reste bornée.

    Elle est exemptée du balayage ci-dessus parce qu'un 200 y est légitime ; ce
    test est la contrepartie qui interdit qu'elle en dise trop.
    """
    reponse = _client_de(patronne).get("/api/bars/", format="json")

    assert reponse.status_code == 200
    assert bar_du_voisin not in {bar["id"] for bar in reponse.json()}
