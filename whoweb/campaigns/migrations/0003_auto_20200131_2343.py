# Generated by Django 2.2.8 on 2020-01-31 23:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0002_auto_20200124_0117"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="intervalcampaignrunner", name="open_credit_budget",
        ),
        migrations.RemoveField(
            model_name="intervalcampaignrunner", name="preset_campaign_list",
        ),
        migrations.RemoveField(
            model_name="intervalcampaignrunner", name="use_credits_method",
        ),
    ]
