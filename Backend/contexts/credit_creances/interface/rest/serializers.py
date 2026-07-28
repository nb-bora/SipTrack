"""Sérialiseurs DRF du contexte Crédit & Créances.

Aucun `auteur_id` en entrée nulle part : il vient du compte authentifié.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers


class CreerClientInputSerializer(serializers.Serializer[Any]):
    bar_id = serializers.CharField(max_length=36)
    nom = serializers.CharField(max_length=120)


class ClientOutputSerializer(serializers.Serializer[Any]):
    id = serializers.CharField()
    bar_id = serializers.CharField()
    nom = serializers.CharField()


class EnregistrerRemboursementInputSerializer(serializers.Serializer[Any]):
    montant = serializers.IntegerField(min_value=1)


class CreditOutputSerializer(serializers.Serializer[Any]):
    id = serializers.CharField()
    client_id = serializers.CharField()
    service_id = serializers.CharField()
    addition_id = serializers.CharField()
    montant = serializers.IntegerField()
    rembourse = serializers.IntegerField()
    reste = serializers.IntegerField()
    statut = serializers.CharField()


class CreanceOutputSerializer(serializers.Serializer[Any]):
    credit_id = serializers.CharField()
    client_id = serializers.CharField()
    client_nom = serializers.CharField()
    service_id = serializers.CharField()
    addition_id = serializers.CharField()
    montant = serializers.IntegerField()
    rembourse = serializers.IntegerField()
    reste = serializers.IntegerField()
    statut = serializers.CharField()


class EncoursClientOutputSerializer(serializers.Serializer[Any]):
    client_id = serializers.CharField()
    client_nom = serializers.CharField()
    total_du = serializers.IntegerField()
    total_rembourse = serializers.IntegerField()
    reste = serializers.IntegerField()
    creances = CreanceOutputSerializer(many=True)
