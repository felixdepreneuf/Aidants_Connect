# Generated by Django 3.1.13 on 2021-11-22 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aidants_connect_web", "0077_aidant_phone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aidant",
            name="phone",
            field=models.TextField(blank=True, verbose_name="Téléphone"),
        ),
    ]
