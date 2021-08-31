# Generated by Django 3.1.12 on 2021-08-17 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aidants_connect_web", "0066_auto_20210817_1128"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journal",
            name="action",
            field=models.CharField(
                choices=[
                    ("connect_aidant", "Connexion d'un aidant"),
                    ("activity_check_aidant", "Reprise de connexion d'un aidant"),
                    ("card_association", "Association d'une carte à d'un aidant"),
                    ("card_validation", "Validation d'une carte associée à un aidant"),
                    ("card_dissociation", "Séparation d'une carte et d'un aidant"),
                    ("franceconnect_usager", "FranceConnexion d'un usager"),
                    ("update_email_usager", "L'email de l'usager a été modifié"),
                    ("update_phone_usager", "Le téléphone de l'usager a été modifié"),
                    ("create_attestation", "Création d'une attestation"),
                    ("create_autorisation", "Création d'une autorisation"),
                    ("use_autorisation", "Utilisation d'une autorisation"),
                    ("cancel_autorisation", "Révocation d'une autorisation"),
                    ("cancel_mandat", "Révocation d'un mandat"),
                    ("import_totp_cards", "Importation de cartes TOTP"),
                    (
                        "init_renew_mandat",
                        "Lancement d'une procédure de renouvellement",
                    ),
                    (
                        "transfer_mandat",
                        "Transférer un mandat à une autre organisation",
                    ),
                ],
                max_length=30,
            ),
        ),
    ]