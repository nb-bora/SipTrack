"""Migration initiale : création de la table Produit."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("gouvernance", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProduitModel",
            fields=[
                ("id", models.CharField(max_length=36, primary_key=True, serialize=False)),
                ("nom", models.CharField(max_length=255)),
                ("quantite", models.IntegerField(default=0)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
                (
                    "bar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="produits",
                        to="gouvernance.barmodel",
                    ),
                ),
            ],
            options={
                "ordering": ["nom"],
            },
        ),
        migrations.AddConstraint(
            model_name="produitmodel",
            constraint=models.UniqueConstraint(
                fields=("bar", "nom"), name="unique_bar_produit_nom"
            ),
        ),
    ]
