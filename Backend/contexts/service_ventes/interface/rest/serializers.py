"""Serializers DRF = frontière DTO.

On utilise des Serializer explicites (jamais ModelSerializer) pour ne pas
ré-exposer l'ORM et garder l'interface découplée du domaine.
"""

from __future__ import annotations

from rest_framework import serializers

from contexts.service_ventes.domain.enums import FormePaiement
from shared.domain.attribution import Capacite


class OuvrirServiceInputSerializer(serializers.Serializer):
    bar_id = serializers.CharField(max_length=36)
    auteur_id = serializers.CharField(max_length=36)
    capacite = serializers.ChoiceField(choices=[c.value for c in Capacite])
    fond_de_caisse = serializers.IntegerField(min_value=0)


class CloturerServiceInputSerializer(serializers.Serializer):
    auteur_id = serializers.CharField(max_length=36)


class ServiceOutputSerializer(serializers.Serializer):
    id = serializers.CharField()
    bar_id = serializers.CharField()
    statut = serializers.CharField()
    fond_de_caisse = serializers.IntegerField()
    ouvert_le = serializers.CharField()
    clos_le = serializers.CharField(required=False, allow_null=True)


class EnregistrerVenteInputSerializer(serializers.Serializer):
    auteur_id = serializers.CharField(max_length=36)
    produit_id = serializers.CharField(max_length=36)
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.IntegerField(min_value=0)
    forme_paiement = serializers.ChoiceField(choices=[f.value for f in FormePaiement])
    # Absent pour une vente au comptoir, qui n'est rattachée à aucune table.
    addition_id = serializers.CharField(max_length=36, required=False, allow_null=True)


class OuvrirAdditionInputSerializer(serializers.Serializer):
    auteur_id = serializers.CharField(max_length=36)
    table_numero = serializers.IntegerField(min_value=1)


class ReglementAdditionInputSerializer(serializers.Serializer):
    auteur_id = serializers.CharField(max_length=36)


class AdditionOutputSerializer(serializers.Serializer):
    id = serializers.CharField()
    service_id = serializers.CharField()
    table_numero = serializers.IntegerField()
    statut = serializers.CharField()
    ouvert_le = serializers.CharField()
    ferme_le = serializers.CharField(required=False, allow_null=True)


class VenteOutputSerializer(serializers.Serializer):
    id = serializers.CharField()
    service_id = serializers.CharField()
    produit_id = serializers.CharField()
    quantite = serializers.IntegerField()
    prix_unitaire = serializers.IntegerField()
    montant_total = serializers.IntegerField()
    forme_paiement = serializers.CharField()
    addition_id = serializers.CharField(required=False, allow_null=True)


class LigneAdditionOutputSerializer(serializers.Serializer):
    vente_id = serializers.CharField()
    produit_id = serializers.CharField()
    quantite = serializers.IntegerField()
    prix_unitaire = serializers.IntegerField()
    montant_total = serializers.IntegerField()
    forme_paiement = serializers.CharField()
    horodatage = serializers.CharField()


class AdditionDetailOutputSerializer(serializers.Serializer):
    id = serializers.CharField()
    service_id = serializers.CharField()
    table_numero = serializers.IntegerField()
    statut = serializers.CharField()
    ouvert_le = serializers.CharField()
    ferme_le = serializers.CharField(required=False, allow_null=True)
    lignes = LigneAdditionOutputSerializer(many=True)
    total = serializers.IntegerField()
