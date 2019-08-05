# Generated by Django 2.2.3 on 2019-08-02 00:45

import functools
import uuid

import django.contrib.postgres.fields.jsonb
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models

import whoweb.contrib.postgres.fields
import whoweb.search.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="SearchExport",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
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
                ("uuid", models.UUIDField(default=uuid.uuid4)),
                (
                    "query",
                    whoweb.contrib.postgres.fields.EmbeddedModelField(
                        default=dict,
                        model_container=whoweb.search.models.FilteredSearchQuery,
                    ),
                ),
                (
                    "validation_list_id",
                    models.CharField(editable=False, max_length=50, null=True),
                ),
                (
                    "columns",
                    whoweb.contrib.postgres.fields.ChoiceArrayField(
                        base_field=models.IntegerField(
                            choices=[
                                (0, "invitekey"),
                                (1, "First Name"),
                                (2, "Last Name"),
                                (3, "Title"),
                                (4, "Company"),
                                (5, "Industry"),
                                (6, "City"),
                                (7, "State"),
                                (8, "Country"),
                                (9, "Profile URL"),
                                (10, "Experience"),
                                (11, "Education"),
                                (12, "Skills"),
                                (13, "Email"),
                                (14, "Email Grade"),
                                (15, "LinkedIn URL"),
                                (16, "Phone Number"),
                                (17, "Additional Emails"),
                                (18, "Facebook"),
                                (19, "Twitter"),
                                (20, "AngelList"),
                                (21, "Google Plus"),
                                (22, "Google Profile"),
                                (23, "Quora"),
                                (24, "GitHub"),
                                (25, "BitBucket"),
                                (26, "StackExchange"),
                                (27, "Flickr"),
                                (28, "YouTube"),
                                (29, "domain"),
                                (30, "mxdomain"),
                            ]
                        ),
                        default=functools.partial(
                            list,
                            *(
                                [
                                    1,
                                    2,
                                    3,
                                    4,
                                    5,
                                    6,
                                    7,
                                    8,
                                    9,
                                    10,
                                    11,
                                    12,
                                    13,
                                    14,
                                    15,
                                    16,
                                    17,
                                ],
                            ),
                            **{}
                        ),
                        size=None,
                    ),
                ),
                (
                    "status",
                    model_utils.fields.StatusField(
                        choices=[
                            ("created", "Created"),
                            ("pages_working", "Pages Running"),
                            ("pages_complete", "Pages Complete"),
                            ("validating", "Awaiting External Validation"),
                            ("post_processing", "Running Post Processing Hooks"),
                            ("complete", "Export Complete"),
                        ],
                        default="created",
                        max_length=100,
                        no_check_for_status=True,
                        verbose_name="status",
                    ),
                ),
                (
                    "status_changed",
                    model_utils.fields.MonitorField(
                        default=django.utils.timezone.now,
                        monitor="status",
                        verbose_name="status changed",
                    ),
                ),
                ("sent", models.CharField(editable=False, max_length=255)),
                (
                    "sent_at",
                    model_utils.fields.MonitorField(
                        default=django.utils.timezone.now,
                        editable=False,
                        monitor="sent",
                        verbose_name="sent at",
                    ),
                ),
                ("progress_counter", models.IntegerField(default=0)),
                ("target", models.IntegerField(default=0)),
                ("notify", models.BooleanField(default=False)),
                ("charge", models.BooleanField(default=False)),
                ("uploadable", models.BooleanField(default=False)),
                ("on_trial", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="SearchExportPage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
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
                ("data", whoweb.contrib.utils.CompressedBinaryField(null=True)),
                ("page", models.PositiveIntegerField()),
                (
                    "working_data",
                    django.contrib.postgres.fields.jsonb.JSONField(editable=False),
                ),
                ("count", models.IntegerField(default=0)),
                ("target", models.IntegerField(null=True)),
                (
                    "export",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="exports.SearchExport",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
    ]
