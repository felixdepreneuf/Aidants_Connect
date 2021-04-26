# Generated by Django 3.1.8 on 2021-05-18 07:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aidants_connect_web', '0055_auto_20210503_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartetotp',
            name='aidant',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='carte_totp', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cartetotp',
            name='serial_number',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
