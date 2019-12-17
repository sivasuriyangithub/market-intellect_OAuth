# Generated by Django 2.2.8 on 2019-12-14 01:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("users", "0004_organizationcredentials")]

    operations = [
        migrations.AlterModelOptions(
            name="group",
            options={
                "permissions": (
                    (
                        "add_organizationcredentials",
                        "May add credentials for this organization",
                    ),
                ),
                "verbose_name": "group",
                "verbose_name_plural": "groups",
            },
        ),
        migrations.AlterField(
            model_name="organizationcredentials",
            name="seat",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="credentials",
                to="users.Seat",
            ),
        ),
    ]