"""Adaptateurs Django du contexte Gouvernance."""

from __future__ import annotations

from contexts.gouvernance_acces.domain.bar import Bar
from contexts.gouvernance_acces.domain.compte import Compte
from contexts.gouvernance_acces.infrastructure.django_app.models import (
    BarModel,
    CompteModel,
)


def _vers_bar(modele: BarModel) -> Bar:
    """Reconstitue un agregat Bar depuis le modèle Django."""
    return Bar(
        id=modele.id,
        nom=modele.nom,
        proprietaire_id=str(modele.proprietaire_id),
    )


def _vers_compte(modele: CompteModel) -> Compte:
    """Reconstitue un agregat Compte depuis le modèle Django."""
    return Compte(
        id=modele.id,
        bar_id=modele.bar_id,
        user_id=str(modele.user_id),
        capacites=frozenset(modele.capacites),
    )


class DjangoBarRepository:
    """Persistence des bars."""

    def ajouter(self, bar: Bar) -> None:
        from django.contrib.auth.models import User

        # Le proprietaire_id est un str (id Django User), converti en int pour la clé étrangère.
        proprietaire = User.objects.get(pk=int(bar.proprietaire_id))
        BarModel.objects.create(
            id=bar.id,
            nom=bar.nom,
            proprietaire=proprietaire,
        )

    def par_id(self, bar_id: str) -> Bar | None:
        modele = BarModel.objects.filter(id=bar_id).first()
        return _vers_bar(modele) if modele is not None else None

    def du_proprietaire(self, proprietaire_id: str) -> tuple[Bar, ...]:
        modeles = BarModel.objects.filter(proprietaire_id=int(proprietaire_id))
        return tuple(_vers_bar(m) for m in modeles)


class DjangoCompteRepository:
    """Persistence des comptes."""

    def ajouter(self, compte: Compte) -> None:
        from django.contrib.auth.models import User

        bar = BarModel.objects.get(id=compte.bar_id)
        user = User.objects.get(pk=compte.user_id)
        CompteModel.objects.create(
            id=compte.id,
            bar=bar,
            user=user,
            capacites=list(compte.capacites),
        )

    def par_id(self, compte_id: str) -> Compte | None:
        modele = CompteModel.objects.filter(id=compte_id).first()
        return _vers_compte(modele) if modele is not None else None

    def du_bar(self, bar_id: str) -> tuple[Compte, ...]:
        modeles = CompteModel.objects.filter(bar_id=bar_id)
        return tuple(_vers_compte(m) for m in modeles)

    def du_bar_et_user(self, *, bar_id: str, user_id: str) -> Compte | None:
        modele = CompteModel.objects.filter(bar_id=bar_id, user_id=user_id).first()
        return _vers_compte(modele) if modele is not None else None

    def mettre_a_jour(self, compte: Compte) -> None:
        CompteModel.objects.filter(id=compte.id).update(
            capacites=list(compte.capacites),
        )
