# Generated by Django 3.1.8 on 2021-06-01 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aidants_connect_web", "0057_auto_20210525_1559"),
    ]

    operations = [
        migrations.AddField(
            model_name="aidant",
            name="validated_cgu_version",
            field=models.TextField(null=True),
        ),
    ]
