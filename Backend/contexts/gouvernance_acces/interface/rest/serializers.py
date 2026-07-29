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
