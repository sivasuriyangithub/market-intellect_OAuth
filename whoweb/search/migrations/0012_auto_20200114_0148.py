# Generated by Django 2.2.8 on 2020-01-14 01:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("search", "0011_searchexport_is_removed")]

    operations = [
        migrations.AlterField(
            model_name="searchexport",
            name="seat",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="users.Seat",
            ),
        )
    ]
