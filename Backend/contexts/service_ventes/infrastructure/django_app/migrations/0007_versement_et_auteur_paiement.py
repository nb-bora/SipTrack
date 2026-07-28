"""Sous-caisse serveuse : versements, et l'auteur porté par le paiement.

`auteur_id` est ajouté à `PaiementModel` : sans lui, on ne peut pas dire **qui**
a encaissé, donc pas réconcilier une sous-caisse. Il n'existait jusqu'ici que
dans l'événement journalisé.

Le défaut vide ne concerne que d'éventuelles lignes antérieures : tout paiement
écrit depuis le code porte son auteur.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("service_ventes", "0006_paiementmodel"),
    ]

    operations = [
        migrations.AddField(
            model_name="paiementmodel",
            name="auteur_id",
            field=models.CharField(default="", max_length=36),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="VersementModel",
            fields=[
                ("id", models.CharField(max_length=36, primary_key=True, serialize=False)),
                ("serveuse_id", models.CharField(max_length=36)),
                ("attendu", models.PositiveIntegerField()),
                ("verse", models.PositiveIntegerField()),
                ("ecart", models.IntegerField()),
                ("horodatage", models.DateTimeField()),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="versements",
                        to="service_ventes.servicemodel",
                    ),
                ),
            ],
            options={
                "db_table": "service_ventes_versement",
                "ordering": ["horodatage"],
            },
        ),
        migrations.AddConstraint(
            model_name="versementmodel",
            constraint=models.UniqueConstraint(
                fields=("service", "serveuse_id"),
                name="un_versement_par_serveuse_et_service",
            ),
        ),
    ]
