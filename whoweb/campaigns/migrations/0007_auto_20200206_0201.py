# Generated by Django 2.2.8 on 2020-02-06 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0006_basecampaignrunner_public_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sendingrule",
            name="include_previous",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="sendingrule",
            name="send_datetime",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="sendingrule",
            name="send_delta",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]