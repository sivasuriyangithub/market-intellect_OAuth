# Generated by Django 2.2.8 on 2020-03-11 00:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("djstripe", "0005_2_2"),
        ("payments", "0009_auto_20200303_1622"),
    ]

    operations = [
        migrations.CreateModel(
            name="WKPlanPreset",
            fields=[
                (
                    "wkplan_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="payments.WKPlan",
                    ),
                ),
                ("stripe_plans", models.ManyToManyField(to="djstripe.Plan")),
            ],
            options={
                "verbose_name": "credit plan factory",
                "verbose_name_plural": "credit plan factories",
            },
            bases=("payments.wkplan",),
        ),
    ]
