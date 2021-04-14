# Generated by Django 2.2.19 on 2021-04-14 02:55

from django.db import migrations
import tagulous.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("coldemail", "0021_auto_20200706_1326"),
        ("search", "0032_auto_20201102_1104"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchexport",
            name="tags",
            field=tagulous.models.fields.TagField(
                _set_tag_meta=True,
                blank=True,
                force_lowercase=True,
                help_text="Enter a comma-separated tag string",
                to="coldemail.ColdEmailTagModel",
            ),
        ),
    ]
