"""Sérialiseurs du contexte Gouvernance."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers


class CreerBarInputSerializer(serializers.Serializer[Any]):
    """Créer un bar (seul le nom ; proprietaire_id vient du jeton)."""

    nom = serializers.CharField(max_length=120)


class BarOutputSerializer(serializers.Serializer[Any]):
    """Représentation d'un bar."""

    id = serializers.CharField()
    nom = serializers.CharField()
    proprietaire_id = serializers.CharField()


class CreerCompteInputSerializer(serializers.Serializer[Any]):
    """Créer un compte utilisateur dans un bar."""

    bar_id = serializers.CharField(max_length=36)
    user_id = serializers.CharField(max_length=36)
    capacites_initiales = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
    )


class CreerEmployeInputSerializer(serializers.Serializer[Any]):
    """Créer un compte pour un nouvel employé (crée aussi le User Django)."""

    bar_id = serializers.CharField(max_length=36)
    username = serializers.CharField(max_length=150)
    mot_de_passe_initial = serializers.CharField(
        max_length=128,
        write_only=True,
        help_text="Mot de passe initial ; doit satisfaire les règles de validation Django.",
    )
    capacites_initiales = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
    )


class CompteOutputSerializer(serializers.Serializer[Any]):
    """Représentation d'un compte utilisateur."""

    id = serializers.CharField()
    bar_id = serializers.CharField()
    user_id = serializers.CharField()
    capacites = serializers.ListField(child=serializers.CharField())


class AccorderCapaciteInputSerializer(serializers.Serializer[Any]):
    """Accorder une capacité à un compte."""

    capacite = serializers.CharField()


class RetirerCapaciteInputSerializer(serializers.Serializer[Any]):
    """Retirer une capacité d'un compte."""

    capacite = serializers.CharField()


class AccesPlateformeOutputSerializer(serializers.Serializer[Any]):
    """Une consultation faite au titre du privilège plateforme."""

    administrateur_id = serializers.CharField()
    operation = serializers.CharField()
    horodatage = serializers.DateTimeField()


class InscrireInputSerializer(serializers.Serializer[Any]):
    """Inscription publique : créer un compte et un premier bar."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)
    email = serializers.EmailField(required=False, default="")
    nom_bar = serializers.CharField(max_length=120)


class InscrireOutputSerializer(serializers.Serializer[Any]):
    """Confirmation d'inscription."""

    user_id = serializers.CharField()
    bar_id = serializers.CharField()
    bar_nom = serializers.CharField()
    message = serializers.CharField()


class ChangerMotDePasseInputSerializer(serializers.Serializer[Any]):
    """Changer le mot de passe de l'utilisateur authentifié."""

    nouveau_mot_de_passe = serializers.CharField(
        max_length=128,
        write_only=True,
        help_text="Nouveau mot de passe ; doit satisfaire les règles de validation Django.",
    )


class ObtenirJetonOutputSerializer(serializers.Serializer[Any]):
    """Réponse d'authentification avec flag mot de passe."""

    token = serializers.CharField()
    doit_changer_mot_de_passe = serializers.BooleanField()
