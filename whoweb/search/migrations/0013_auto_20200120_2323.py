# Generated by Django 2.2.8 on 2020-01-20 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0012_auto_20200114_0148"),
    ]

    operations = [
        migrations.AlterField(
            model_name="searchexport",
            name="validation_list_id",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]