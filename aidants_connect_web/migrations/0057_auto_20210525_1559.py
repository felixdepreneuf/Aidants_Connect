# Generated by Django 3.1.8 on 2021-05-25 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aidants_connect_web", "0056_auto_20210518_0952"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aidant",
            name="can_create_mandats",
            field=models.BooleanField(
                default=True,
                help_text="Précise si l’utilisateur peut accéder à l’espace aidant pour créer des mandats.",
                verbose_name="Aidant - Peut créer des mandats",
            ),
        ),
        migrations.AlterField(
            model_name="journal",
            name="action",
            field=models.CharField(
                choices=[
                    ("connect_aidant", "Connexion d'un aidant"),
                    ("activity_check_aidant", "Reprise de connexion d'un aidant"),
                    ("franceconnect_usager", "FranceConnexion d'un usager"),
                    ("update_email_usager", "L'email de l'usager a été modifié"),
                    ("update_phone_usager", "Le téléphone de l'usager a été modifié"),
                    ("create_attestation", "Création d'une attestation"),
                    ("create_autorisation", "Création d'une autorisation"),
                    ("use_autorisation", "Utilisation d'une autorisation"),
                    ("cancel_autorisation", "Révocation d'une autorisation"),
                    ("import_totp_cards", "Importation de cartes TOTP"),
                    (
                        "init_renew_mandat",
                        "Lancement d'une procédure de renouvellement",
                    ),
                ],
                max_length=30,
            ),
        ),
    ]