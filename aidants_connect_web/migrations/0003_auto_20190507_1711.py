# Generated by Django 2.2 on 2019-05-07 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("aidants_connect_web", "0002_connection_nonce")]

    operations = [
        migrations.AlterField(
            model_name="connection",
            name="nonce",
            field=models.TextField(default="No Nonce Provided"),
        )
    ]
