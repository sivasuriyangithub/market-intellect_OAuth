# Generated by Django 2.2.8 on 2020-01-23 22:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import whoweb.contrib.postgres.fields
import whoweb.contrib.postgres.utils
import whoweb.search.models.embedded


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0010_auto_20191217_0651"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("search", "0013_auto_20200120_2323"),
        ("coldemail", "0008_auto_20200122_2326"),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseCampaignRunner",
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
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("is_removed", models.BooleanField(default=False)),
                ("title", models.CharField(max_length=255)),
                (
                    "query",
                    whoweb.contrib.postgres.fields.EmbeddedModelField(
                        default=whoweb.search.models.embedded.FilteredSearchQuery,
                        encoder=whoweb.contrib.postgres.utils.EmbeddedJSONEncoder,
                        model_container=whoweb.search.models.embedded.FilteredSearchQuery,
                    ),
                ),
                ("budget", models.PositiveIntegerField()),
                ("published", models.DateTimeField(null=True)),
                (
                    "status",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (0, "Draft"),
                            (2, "Pending"),
                            (4, "Paused"),
                            (8, "Published"),
                            (16, "Running"),
                            (32, "Sending"),
                            (128, "Complete"),
                        ],
                        db_index=True,
                        default=0,
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
                (
                    "tracking_params",
                    django.contrib.postgres.fields.jsonb.JSONField(null=True),
                ),
                (
                    "campaigns",
                    models.ManyToManyField(
                        related_name="_basecampaignrunner_campaigns_+",
                        to="coldemail.ColdCampaign",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="SendingRule",
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
                ("index", models.PositiveIntegerField()),
                (
                    "trigger",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "At a specified time"),
                            (1, "Seconds after previous"),
                            (2, "A short delay after creation"),
                        ],
                        default=2,
                    ),
                ),
                ("send_datetime", models.DateTimeField(null=True)),
                ("send_delta", models.PositiveIntegerField(null=True)),
                ("include_previous", models.BooleanField(default=False)),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="coldemail.CampaignMessage",
                    ),
                ),
                (
                    "message_template",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="coldemail.CampaignMessageTemplate",
                    ),
                ),
                (
                    "runner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="campaigns.BaseCampaignRunner",
                    ),
                ),
            ],
            options={"unique_together": {("runner", "index")},},
        ),
        migrations.CreateModel(
            name="DripRecord",
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
                ("order", models.PositiveSmallIntegerField(default=0)),
                (
                    "drip",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="in_drip_drips",
                        to="coldemail.ColdCampaign",
                    ),
                ),
                (
                    "root",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="in_drip_roots",
                        to="coldemail.ColdCampaign",
                    ),
                ),
                (
                    "runner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="campaigns.BaseCampaignRunner",
                    ),
                ),
            ],
            options={"unique_together": {("runner", "order")},},
        ),
        migrations.AddField(
            model_name="basecampaignrunner",
            name="drips",
            field=models.ManyToManyField(
                related_name="_basecampaignrunner_drips_+",
                through="campaigns.DripRecord",
                to="coldemail.ColdCampaign",
            ),
        ),
        migrations.AddField(
            model_name="basecampaignrunner",
            name="messages",
            field=models.ManyToManyField(
                through="campaigns.SendingRule", to="coldemail.CampaignMessage"
            ),
        ),
        migrations.AddField(
            model_name="basecampaignrunner",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_campaigns.basecampaignrunner_set+",
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AddField(
            model_name="basecampaignrunner",
            name="scroll",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="search.ScrollSearch",
            ),
        ),
        migrations.AddField(
            model_name="basecampaignrunner",
            name="seat",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="users.Seat",
            ),
        ),
        migrations.CreateModel(
            name="SimpleDripCampaignRunner",
            fields=[
                (
                    "basecampaignrunner_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="campaigns.BaseCampaignRunner",
                    ),
                ),
                (
                    "use_credits_method",
                    models.CharField(blank=True, max_length=63, null=True),
                ),
                ("open_credit_budget", models.IntegerField()),
                (
                    "preset_campaign_list",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="coldemail.CampaignList",
                    ),
                ),
            ],
            options={"abstract": False,},
            bases=("campaigns.basecampaignrunner",),
        ),
        migrations.CreateModel(
            name="IntervalCampaignRunner",
            fields=[
                (
                    "basecampaignrunner_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="campaigns.BaseCampaignRunner",
                    ),
                ),
                (
                    "interval_hours",
                    models.PositiveIntegerField(
                        default=24, help_text="Interval between each campaign."
                    ),
                ),
                (
                    "max_sends",
                    models.PositiveIntegerField(
                        help_text="Total campaigns allowed for this manager.", null=True
                    ),
                ),
                (
                    "use_credits_method",
                    models.CharField(blank=True, max_length=63, null=True),
                ),
                ("open_credit_budget", models.IntegerField()),
                (
                    "preset_campaign_list",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="coldemail.CampaignList",
                    ),
                ),
            ],
            options={"abstract": False,},
            bases=("campaigns.basecampaignrunner",),
        ),
    ]
