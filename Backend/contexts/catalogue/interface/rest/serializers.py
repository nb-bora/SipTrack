"""Sérialiseurs DRF du contexte Catalogue."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers


class InscrireProduitInputSerializer(serializers.Serializer[Any]):
    bar_id = serializers.CharField(max_length=36)
    nom = serializers.CharField(max_length=120)
    prix = serializers.IntegerField(min_value=1)


class ChangerLeTarifInputSerializer(serializers.Serializer[Any]):
    prix = serializers.IntegerField(min_value=1)


class ProduitOutputSerializer(serializers.Serializer[Any]):
    id = serializers.CharField()
    bar_id = serializers.CharField()
    nom = serializers.CharField()
    prix = serializers.IntegerField()
    en_vente = serializers.BooleanField()
