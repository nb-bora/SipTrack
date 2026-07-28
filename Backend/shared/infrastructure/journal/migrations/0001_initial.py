"""Reprise du journal, jusqu'ici propriété de service_ventes.

La table existe déjà (`service_ventes_mouvement`) et contient des Faits. On ne
la recrée donc pas : `SeparateDatabaseAndState` déclare le modèle dans cette
application **sans toucher à la base**, puis un simple renommage aligne le nom
physique sur le nouveau propriétaire. Détruire et recréer la table reviendrait à
effacer le journal — l'exact contraire de sa raison d'être.
"""

from django.db import migrations, models
from django.core.serializers.json import DjangoJSONEncoder


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("service_ventes", "0004_ventemodel_addition"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Rien à faire en base : la table est déjà là.
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="MouvementModel",
                    fields=[
                        (
                            "id",
                            models.CharField(max_length=36, primary_key=True, serialize=False),
                        ),
                        ("type", models.CharField(max_length=60)),
                        ("auteur_id", models.CharField(max_length=36)),
                        (
                            "donnees",
                            models.JSONField(default=dict, encoder=DjangoJSONEncoder),
                        ),
                        ("horodatage_saisie", models.DateTimeField()),
                        ("horodatage_reception", models.DateTimeField(auto_now_add=True)),
                    ],
                    options={
                        "db_table": "service_ventes_mouvement",
                        "ordering": ["horodatage_reception"],
                    },
                ),
            ],
        ),
        # Renommage physique : le journal n'appartient plus à service_ventes.
        migrations.AlterModelTable(
            name="mouvementmodel",
            table="journal_mouvement",
        ),
    ]
