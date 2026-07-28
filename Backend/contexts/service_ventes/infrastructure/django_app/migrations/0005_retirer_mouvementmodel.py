"""service_ventes cède le journal.

Seul l'état Django change : la table a déjà été reprise (et renommée) par
l'application `journal`. Aucune opération en base ici, sous peine de supprimer
la table que l'autre application vient d'adopter.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("service_ventes", "0004_ventemodel_addition"),
        ("journal", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="MouvementModel"),
            ],
        ),
    ]
