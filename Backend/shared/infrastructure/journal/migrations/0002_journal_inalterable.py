"""Le journal devient réellement inaltérable.

Trois temps : on ajoute les colonnes de chaînage, on les remplit pour les
Mouvements déjà écrits, puis on pose le déclencheur qui refuse toute
modification. L'ordre compte — le remplissage a besoin d'écrire, ce que le
déclencheur interdira ensuite.
"""

from django.db import migrations, models

from shared.infrastructure.journal.empreinte import GENESE, calculer_empreinte

_CREER_GARDE = """
CREATE OR REPLACE FUNCTION journal_refuser_alteration() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION
        'Le journal est append-only : un Mouvement ne se modifie ni ne se supprime. '
        'Une correction s''ecrit par contre-passation.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER journal_mouvement_pas_d_alteration
    BEFORE UPDATE OR DELETE ON journal_mouvement
    FOR EACH ROW EXECUTE FUNCTION journal_refuser_alteration();

CREATE TRIGGER journal_mouvement_pas_de_troncature
    BEFORE TRUNCATE ON journal_mouvement
    FOR EACH STATEMENT EXECUTE FUNCTION journal_refuser_alteration();
"""

_RETIRER_GARDE = """
DROP TRIGGER IF EXISTS journal_mouvement_pas_de_troncature ON journal_mouvement;
DROP TRIGGER IF EXISTS journal_mouvement_pas_d_alteration ON journal_mouvement;
DROP FUNCTION IF EXISTS journal_refuser_alteration();
"""


def chainer_les_mouvements_existants(apps, schema_editor):
    """Signe l'historique déjà écrit, dans son ordre d'arrivée."""
    modele_mouvement = apps.get_model("journal", "MouvementModel")
    empreinte_precedente = GENESE

    for sequence, mouvement in enumerate(
        modele_mouvement.objects.order_by("horodatage_reception", "id"), start=1
    ):
        mouvement.sequence = sequence
        mouvement.empreinte_precedente = empreinte_precedente
        mouvement.empreinte = calculer_empreinte(
            identifiant=mouvement.id,
            type_evenement=mouvement.type,
            auteur_id=mouvement.auteur_id,
            donnees=mouvement.donnees,
            horodatage_saisie=mouvement.horodatage_saisie,
            sequence=sequence,
            empreinte_precedente=empreinte_precedente,
        )
        mouvement.save(update_fields=["sequence", "empreinte", "empreinte_precedente"])
        empreinte_precedente = mouvement.empreinte


def rien_a_defaire(apps, schema_editor):
    """Le retour arrière supprime les colonnes : rien à dé-signer."""


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0001_initial"),
    ]

    operations = [
        # 1. Colonnes nullables, le temps de remplir l'existant.
        migrations.AddField(
            model_name="mouvementmodel",
            name="sequence",
            field=models.BigIntegerField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="mouvementmodel",
            name="empreinte",
            field=models.CharField(max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="mouvementmodel",
            name="empreinte_precedente",
            field=models.CharField(max_length=64, null=True),
        ),
        # 2. Signature de l'historique déjà écrit.
        migrations.RunPython(chainer_les_mouvements_existants, rien_a_defaire),
        # 3. Les colonnes deviennent obligatoires.
        migrations.AlterField(
            model_name="mouvementmodel",
            name="sequence",
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name="mouvementmodel",
            name="empreinte",
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name="mouvementmodel",
            name="empreinte_precedente",
            field=models.CharField(max_length=64),
        ),
        migrations.AlterModelOptions(
            name="mouvementmodel",
            options={"ordering": ["sequence"]},
        ),
        # 4. La garde en base, qui protège aussi d'un accès direct.
        migrations.RunSQL(sql=_CREER_GARDE, reverse_sql=_RETIRER_GARDE),
    ]
