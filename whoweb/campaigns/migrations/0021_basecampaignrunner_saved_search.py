# Generated by Django 2.2.19 on 2021-07-01 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0020_auto_20210413_1955"),
    ]

    operations = [
        migrations.AddField(
            model_name="basecampaignrunner",
            name="saved_search",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
