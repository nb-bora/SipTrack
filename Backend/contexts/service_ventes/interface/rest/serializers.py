"""Serializers DRF = frontière DTO.

On utilise des Serializer explicites (jamais ModelSerializer) pour ne pas
ré-exposer l'ORM et garder l'interface découplée du domaine.
"""

from __future__ import annotations

from rest_framework import serializers

from shared.domain.attribution import Capacite


class OuvrirServiceInputSerializer(serializers.Serializer):
    bar_id = serializers.CharField(max_length=36)
    auteur_id = serializers.CharField(max_length=36)
    capacite = serializers.ChoiceField(choices=[c.value for c in Capacite])
    fond_de_caisse = serializers.IntegerField(min_value=0)


class ServiceOutputSerializer(serializers.Serializer):
    id = serializers.CharField()
    bar_id = serializers.CharField()
    statut = serializers.CharField()
    fond_de_caisse = serializers.IntegerField()
    ouvert_le = serializers.CharField()
