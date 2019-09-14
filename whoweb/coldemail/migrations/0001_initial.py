# Generated by Django 2.2.3 on 2019-09-12 23:55

import bson.objectid
from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ReplyTo",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "id",
                    models.CharField(
                        default=bson.objectid.ObjectId,
                        max_length=100,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("mailgun_route_id", models.CharField(max_length=50, null=True)),
                (
                    "coldemail_route_id",
                    models.CharField(
                        help_text="ID of reply route in ColdEmail Router.",
                        max_length=50,
                        null=True,
                    ),
                ),
                ("from_name", models.CharField(default="", max_length=255)),
            ],
            options={"abstract": False},
        )
    ]
