# Generated by Django 2.2.3 on 2019-08-29 23:45

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("search", "0003_auto_20190829_2345")]

    operations = [
        migrations.AlterField(
            model_name="mxdomain",
            name="mxs",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=255), default=list, size=None
            ),
        )
    ]
