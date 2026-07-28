"""Serializers pour l'API REST de Stock & Inventaire."""

from rest_framework import serializers


class CreerProduitInputSerializer(serializers.Serializer):
    """Entrée pour créer un produit."""

    bar_id = serializers.CharField(max_length=36)
    nom = serializers.CharField(max_length=255)
    quantite_initiale = serializers.IntegerField(min_value=0)


class InventaireProduitOutputSerializer(serializers.Serializer):
    """Sortie pour un produit en stock."""

    id = serializers.CharField(read_only=True)
    bar_id = serializers.CharField(read_only=True)
    nom = serializers.CharField(read_only=True)
    quantite = serializers.IntegerField(read_only=True)


class AjouterStockInputSerializer(serializers.Serializer):
    """Entrée pour ajouter du stock."""

    quantite = serializers.IntegerField(min_value=0)


class VendreInputSerializer(serializers.Serializer):
    """Entrée pour enregistrer une vente."""

    quantite = serializers.IntegerField(min_value=0)


class CorrigerInventaireInputSerializer(serializers.Serializer):
    """Entrée pour corriger l'inventaire."""

    quantite_nouvelle = serializers.IntegerField(min_value=0)
    raison = serializers.CharField(max_length=255)
