# Generated by Django 3.1.13 on 2021-12-06 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aidants_connect_web", "0078_auto_20211122_1813"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisation",
            name="city",
            field=models.CharField(max_length=255, null=True, verbose_name="Ville"),
        ),
    ]
