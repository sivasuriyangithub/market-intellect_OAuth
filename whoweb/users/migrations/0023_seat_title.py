# Generated by Django 2.2.10 on 2020-08-13 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0022_auto_20200702_1938"),
    ]

    operations = [
        migrations.AddField(
            model_name="seat",
            name="title",
            field=models.CharField(
                blank=True, help_text="Title within organization", max_length=255
            ),
        ),
    ]