"""Ce que le durcissement doit garantir, éprouvé plutôt qu'annoncé.

Quatre points de l'audit technique, chacun avec son test : la clé de repli, le
débit non limité, les jetons éternels, et le hachage des mots de passe.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from conftest import ClientAvecCleIdempotente


@pytest.fixture(autouse=True)
def _cache_vierge() -> Any:
    """Les compteurs de débit vivent dans le cache : sans purge, ils fuient.

    Un test qui consomme son quota ferait échouer le suivant, et l'ordre
    d'exécution deviendrait significatif — la pire sorte de test instable.
    """
    cache.clear()
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# S1 — la clé de repli
# ---------------------------------------------------------------------------


def test_la_production_refuse_de_demarrer_sans_secret_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le repli de `base.py` ne doit jamais servir en production.

    Il est **publié dans un dépôt public**. Une application qui démarre avec lui
    signe jetons et cookies avec une clé que tout le monde peut lire — et rien
    ne le signale, puisqu'elle démarre.
    """
    from config.settings.prod import ConfigurationManquante, _exiger

    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ConfigurationManquante, match="SECRET_KEY"):
        _exiger("SECRET_KEY")


def test_la_production_accepte_une_cle_fournie(monkeypatch: pytest.MonkeyPatch) -> None:
    """La contrepartie : le garde ne doit pas bloquer un démarrage légitime."""
    from config.settings.prod import _exiger

    monkeypatch.setenv("SECRET_KEY", "une-cle-de-production")

    assert _exiger("SECRET_KEY") == "une-cle-de-production"


def test_une_cle_vide_vaut_une_cle_absente(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une variable déclarée mais vide est une erreur de configuration courante."""
    from config.settings.prod import ConfigurationManquante, _exiger

    monkeypatch.setenv("SECRET_KEY", "   ")

    with pytest.raises(ConfigurationManquante):
        _exiger("SECRET_KEY")


# ---------------------------------------------------------------------------
# S2 — la limitation de débit
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_le_freinage_s_applique_reellement(auteur: Any, mot_de_passe: str) -> None:
    """Éprouve le débit **tel qu'il est configuré**, sans rien mutiler.

    `override_settings` sur `REST_FRAMEWORK` prend effet mais **ne se restaure
    pas** pour DRF : le débit réduit fuyait dans les tests suivants et rendait
    leur résultat dépendant de l'ordre. Mieux vaut consommer un quota réel.

    Celui de l'obtention de jeton — 10/min — est le plus bas, donc le seul
    atteignable sans des centaines d'appels. C'est aussi celui qui compte : il
    freine le bourrinage de mots de passe.
    """
    auteur.set_password(mot_de_passe)
    auteur.save(update_fields=["password"])

    codes = [
        APIClient()
        .post(
            "/api/auth/jeton/",
            {"username": auteur.username, "password": "mauvais"},
            format="json",
        )
        .status_code
        for _ in range(12)
    ]

    assert 429 in codes, f"Aucun freinage sur 12 tentatives : {codes}"


@pytest.mark.django_db
def test_le_travail_courant_n_est_pas_freine(client_api: APIClient, bar_de_test: str) -> None:
    """Brider le travail légitime ferait contourner l'outil.

    Une serveuse en coup de feu saisit vite. Un plafond trop bas coûterait plus
    cher que l'abus qu'il prévient — d'où 300/min, largement au-dessus de
    l'usage réel.
    """
    codes = [
        client_api.get(f"/api/bars/{bar_de_test}/encours/", format="json").status_code
        for _ in range(30)
    ]

    assert codes == [200] * 30


@pytest.mark.django_db
def test_la_sonde_de_sante_echappe_au_freinage() -> None:
    """Render l'interroge en continu, la CI en boucle.

    La soumettre au quota anonyme la ferait échouer précisément quand on en a
    besoin : pendant un incident, ou pendant un déploiement.
    """
    codes = [APIClient().get("/api/sante/", format="json").status_code for _ in range(40)]

    assert codes == [200] * 40


# ---------------------------------------------------------------------------
# S3 — l'expiration et la révocation des jetons
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_un_jeton_perime_n_ouvre_plus_rien(auteur: Any, bar_de_test: str) -> None:
    """Un téléphone volé ne doit pas donner un accès à vie."""
    from rest_framework.authtoken.models import Token

    jeton = Token.objects.create(user=auteur)
    jeton.created = timezone.now() - timedelta(days=settings.JETON_DUREE_JOURS + 1)
    jeton.save(update_fields=["created"])

    client = ClientAvecCleIdempotente()
    client.credentials(HTTP_AUTHORIZATION=f"Token {jeton.key}")
    reponse = client.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    assert reponse.status_code == 401


@pytest.mark.django_db
def test_un_jeton_perime_est_supprime(auteur: Any, bar_de_test: str) -> None:
    """Le laisser dormir ferait grossir une table de jetons morts.

    Et le supprimer rend le refus définitif : un jeton expiré ne redevient pas
    valide si l'horloge recule.
    """
    from rest_framework.authtoken.models import Token

    jeton = Token.objects.create(user=auteur)
    jeton.created = timezone.now() - timedelta(days=settings.JETON_DUREE_JOURS + 1)
    jeton.save(update_fields=["created"])

    client = ClientAvecCleIdempotente()
    client.credentials(HTTP_AUTHORIZATION=f"Token {jeton.key}")
    client.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    assert not Token.objects.filter(key=jeton.key).exists()


@pytest.mark.django_db
def test_un_jeton_valide_continue_d_ouvrir(client_api: APIClient, bar_de_test: str) -> None:
    """La contrepartie : l'expiration ne doit pas gêner l'usage courant."""
    reponse = client_api.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    assert reponse.status_code == 200


@pytest.mark.django_db
def test_la_deconnexion_revoque_le_jeton(client_api: APIClient, bar_de_test: str) -> None:
    """Une révocation qui suppose un accès à la base n'est pas une révocation."""
    assert client_api.post("/api/auth/deconnexion/", {}, format="json").status_code == 204

    apres = client_api.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    assert apres.status_code == 401


# ---------------------------------------------------------------------------
# Hachage des mots de passe
# ---------------------------------------------------------------------------


def test_argon2_est_le_hachage_de_production() -> None:
    """PBKDF2 ne fait que multiplier les itérations ; Argon2id résiste au GPU.

    La suite tourne avec un hachage rapide (cf. `config/settings/test.py`) :
    c'est donc la configuration de production qu'on inspecte ici, pas celle
    sous laquelle ce test s'exécute.
    """
    from config.settings import base

    assert base.PASSWORD_HASHERS[0].endswith("Argon2PasswordHasher")


@pytest.mark.django_db
def test_le_hachage_argon2_fonctionne_reellement(django_user_model: Any) -> None:
    """Déclarer l'algorithme ne suffit pas : il doit produire un mot de passe."""
    from django.test import override_settings

    with override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.Argon2PasswordHasher"]):
        personne = django_user_model.objects.create_user(
            username="hachage", password="un-mot-de-passe-solide"
        )

        assert personne.password.startswith("argon2$")
        assert personne.check_password("un-mot-de-passe-solide")


def test_un_ancien_hachage_reste_verifiable(django_user_model: Any) -> None:
    """Changer d'algorithme ne doit enfermer personne dehors.

    Les comptes créés avant Argon2 continuent de se connecter. On active ici la
    configuration de production, PBKDF2 y étant déclaré en second recours
    (`config/settings/base.py`) — la suite tourne sous un hachage différent,
    voir `config/settings/test.py`.
    """
    from django.contrib.auth.hashers import make_password
    from django.test import override_settings

    from config.settings.base import PASSWORD_HASHERS

    with override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS):
        personne = django_user_model.objects.create_user(username="ancien")
        personne.password = make_password("mot-de-passe-ancien", hasher="pbkdf2_sha256")
        personne.save(update_fields=["password"])

        assert personne.check_password("mot-de-passe-ancien")
