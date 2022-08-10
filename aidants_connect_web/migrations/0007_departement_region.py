# Generated by Django 3.2.12 on 2022-08-10 16:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aidants_connect_web', '0006_auto_20220809_1721'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Nom de région')),
                ('codeinsee', models.CharField(max_length=2, unique=True, verbose_name='Code INSEE')),
            ],
        ),
        migrations.CreateModel(
            name='Departement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Nom du département')),
                ('codeinsee', models.CharField(max_length=3, unique=True, verbose_name='Code INSEE')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aidants_connect_web.region')),
            ],
        ),
    ]
