# Generated by Django 2.2.10 on 2020-05-27 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0029_searchexport_extra_columns"),
    ]

    operations = [
        migrations.AlterField(
            model_name="derivationcache",
            name="profile_id",
            field=models.CharField(max_length=255),
        ),
    ]
