# Generated by Django 2.2.8 on 2020-03-24 23:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0018_auto_20200324_1622"),
    ]

    operations = [
        migrations.CreateModel(
            name="WKPlanPresetTag",
            fields=[
                (
                    "tag",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                (
                    "preset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="payments.WKPlanPreset",
                    ),
                ),
            ],
        ),
    ]
