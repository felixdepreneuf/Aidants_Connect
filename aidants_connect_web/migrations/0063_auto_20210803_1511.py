# Generated by Django 3.1.12 on 2021-08-03 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aidants_connect_web", "0062_auto_20210712_1644"),
    ]

    operations = [
        migrations.AlterField(
            model_name="connection",
            name="duree_keyword",
            field=models.CharField(
                choices=[
                    ("SHORT", "pour une durée de 1 jour"),
                    ("SEMESTER", "pour une durée de six mois (182) jours"),
                    ("LONG", "pour une durée de 1 an"),
                    ("EUS_03_20", "jusqu’à la fin de l’état d’urgence sanitaire "),
                ],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="mandat",
            name="duree_keyword",
            field=models.CharField(
                choices=[
                    ("SHORT", "pour une durée de 1 jour"),
                    ("SEMESTER", "pour une durée de six mois (182) jours"),
                    ("LONG", "pour une durée de 1 an"),
                    ("EUS_03_20", "jusqu’à la fin de l’état d’urgence sanitaire "),
                ],
                max_length=16,
                null=True,
                verbose_name="Durée",
            ),
        ),
    ]
