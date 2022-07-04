# Generated by Django 3.2.12 on 2022-05-11 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aidants_connect_web', '0001_20220329_stable_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='habilitationrequest',
            name='date_test_pix',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date test PIX'),
        ),
        migrations.AddField(
            model_name='habilitationrequest',
            name='test_pix_passed',
            field=models.BooleanField(default=False, verbose_name='Test PIX'),
        ),
    ]
