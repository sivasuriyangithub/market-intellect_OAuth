# Generated by Django 2.2.19 on 2021-09-09 18:34

from django.db import migrations, models
import django.db.models.deletion
import whoweb.contrib.fields


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0034_auto_20201113_1309"),
        ("campaigns", "0022_auto_20210716_1102"),
    ]

    operations = [
        migrations.CreateModel(
            name="IcebreakerTemplate",
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
                ("is_removed", models.BooleanField(default=False)),
                (
                    "public_id",
                    models.CharField(
                        default=whoweb.contrib.fields.random_public_id,
                        editable=False,
                        help_text="Public ID of the object.",
                        max_length=16,
                        unique=True,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
                (
                    "billing_seat",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="payments.BillingAccountMember",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.AddField(
            model_name="sendingrule",
            name="icebreaker_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="campaigns.IcebreakerTemplate",
            ),
        ),
    ]