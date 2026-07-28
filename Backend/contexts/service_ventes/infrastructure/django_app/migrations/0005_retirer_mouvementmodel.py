"""service_ventes cède le journal.

Seul l'état Django change : la table a déjà été reprise (et renommée) par
l'application `journal`. Aucune opération en base ici, sous peine de supprimer
la table que l'autre application vient d'adopter.

⚠️ **Retour arrière : tout ou rien.** Annuler cette seule migration restaure le
modèle dans l'état de `service_ventes` alors que la table s'appelle désormais
`journal_mouvement` — le code chercherait une table inexistante. Le retour doit
défaire les deux migrations, dans cet ordre :

    python manage.py migrate service_ventes 0004
    python manage.py migrate journal zero

À l'issue de quoi la table reprend son nom d'origine et l'état redevient
cohérent. Un retour partiel, lui, laisse le projet dans un état bancal.
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
