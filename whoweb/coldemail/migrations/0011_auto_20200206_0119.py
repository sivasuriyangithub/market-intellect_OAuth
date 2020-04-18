# Generated by Django 2.2.8 on 2020-02-06 01:19

import whoweb.contrib.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coldemail", "0010_auto_20200201_0047"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaignlist",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                unique=True,
                verbose_name="ID",
            ),
        ),
        migrations.AddField(
            model_name="campaignmessage",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                unique=True,
                verbose_name="ID",
            ),
        ),
        migrations.AddField(
            model_name="coldcampaign",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                unique=True,
                verbose_name="ID",
            ),
        ),
        migrations.AddField(
            model_name="singlecoldemail",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                unique=True,
                verbose_name="ID",
            ),
        ),
    ]