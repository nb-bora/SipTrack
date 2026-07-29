"""Ce qui est observé, et surtout ce qui ne l'est pas.

L'observabilité doit permettre un audit minutieux sans devenir elle-même un
passif. Deux exigences opposées, éprouvées ici :

- assez d'information pour reconstituer ce qui s'est passé ;
- **aucune copie** des données sensibles, et un volume borné — la base est
  partagée avec le produit.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from django.test import override_settings as settings_temporaires
from rest_framework.test import APIClient

from shared.infrastructure.observabilite.journalisation import FormatteurJSON
from shared.infrastructure.observabilite.middleware import EN_TETE_CORRELATION


@pytest.mark.django_db
def test_chaque_reponse_porte_un_identifiant_de_correlation(
    client_api: APIClient, bar_de_test: str
) -> None:
    """C'est lui qui relie une plainte d'utilisateur aux lignes de log.

    Sans identifiant rendu au client, « ça a planté vers 21 h » reste la seule
    piste, et l'on cherche à l'œil dans les logs de la soirée.
    """
    reponse = client_api.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    assert reponse.headers[EN_TETE_CORRELATION]


@pytest.mark.django_db
def test_l_identifiant_fourni_par_l_appelant_est_conserve(
    client_api: APIClient, bar_de_test: str
) -> None:
    """Une requête rejouée par l'app mobile garde le même fil.

    Reprendre l'identifiant plutôt qu'en forger un permet de suivre un appel de
    bout en bout, du terminal jusqu'ici.
    """
    reponse = client_api.get(
        f"/api/bars/{bar_de_test}/encours/",
        format="json",
        headers={EN_TETE_CORRELATION: "trace-connue"},
    )

    assert reponse.headers[EN_TETE_CORRELATION] == "trace-connue"


@pytest.mark.django_db
def test_la_ligne_de_log_dit_qui_quoi_et_combien_de_temps(
    client_api: APIClient, bar_de_test: str, auteur: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Les quatre informations qui rendent un audit possible."""
    with caplog.at_level(logging.INFO, logger="siptrack.requete"):
        client_api.get(f"/api/bars/{bar_de_test}/encours/", format="json")

    # Les champs posés par `extra=` vivent dans `__dict__` : c'est exactement là
    # que le formatteur va les chercher, donc c'est là qu'il faut les éprouver.
    ligne = next(e.__dict__ for e in caplog.records if e.name == "siptrack.requete")
    assert ligne["methode"] == "GET"
    assert ligne["chemin"] == f"/api/bars/{bar_de_test}/encours/"
    assert ligne["statut"] == 200
    assert ligne["auteur_id"] == str(auteur.pk)
    assert ligne["duree_ms"] >= 0


@pytest.mark.django_db
def test_aucun_corps_de_requete_ne_part_dans_les_logs(
    client_api: APIClient, bar_de_test: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Le point qui compte le plus.

    Les corps portent des noms de clients, des dettes, des montants. En garder
    une copie dans les logs créerait un second exemplaire des données sensibles,
    moins bien protégé que l'original — un passif, pas un actif.
    """
    with caplog.at_level(logging.INFO):
        client_api.post(
            "/api/clients/",
            {"bar_id": bar_de_test, "nom": "Mme Ngo Bikai"},
            format="json",
        )

    tout = " ".join(
        json.dumps(e.__dict__, default=str) for e in caplog.records if e.name == "siptrack.requete"
    )
    assert "Ngo Bikai" not in tout


def test_le_formatteur_produit_une_ligne_json_exploitable() -> None:
    """Du texte libre se cherche à l'œil ; du JSON se filtre."""
    enregistrement = logging.LogRecord(
        name="siptrack.requete",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="requete",
        args=None,
        exc_info=None,
    )
    enregistrement.__dict__["correlation_id"] = "abc"
    enregistrement.__dict__["duree_ms"] = 12.5

    charge = json.loads(FormatteurJSON().format(enregistrement))

    assert charge["message"] == "requete"
    assert charge["niveau"] == "INFO"
    assert charge["correlation_id"] == "abc"
    assert charge["duree_ms"] == 12.5


def test_le_formatteur_ne_casse_pas_sur_un_objet_non_serialisable() -> None:
    """Perdre une ligne de log coûterait plus que l'approximer."""
    enregistrement = logging.LogRecord(
        name="x", level=logging.INFO, pathname=__file__, lineno=1, msg="m", args=None, exc_info=None
    )
    enregistrement.__dict__["objet"] = object()

    charge = json.loads(FormatteurJSON().format(enregistrement))

    assert "objet" in charge


@pytest.mark.django_db
def test_les_erreurs_client_ne_sont_pas_conservees(client_api: APIClient) -> None:
    """Un client qui envoie n'importe quoi n'est pas un incident.

    Les enregistrer noierait les vraies pannes sous le bruit.
    """
    from shared.infrastructure.observabilite.models import ErreurTechnique

    client_api.post("/api/services/", {"bar_id": "inexistant"}, format="json")

    assert ErreurTechnique.objects.count() == 0


@pytest.mark.django_db
def test_la_table_des_erreurs_est_bornee() -> None:
    """Un module qui observe ne doit pas pouvoir faire tomber ce qu'il observe.

    La base est partagée avec les données du produit. Une boucle d'erreurs est
    précisément le moment où ce garde sert.
    """
    from shared.infrastructure.observabilite.middleware import ObservabiliteMiddleware
    from shared.infrastructure.observabilite.models import ErreurTechnique

    plafond = 5
    with settings_temporaires(OBSERVABILITE_ERREURS_MAX=plafond):
        for _ in range(plafond * 4):
            ErreurTechnique.objects.create(
                correlation_id="x", methode="GET", chemin="/api/x/", statut=500
            )
            ObservabiliteMiddleware._elaguer()

    assert ErreurTechnique.objects.count() <= plafond + 1
