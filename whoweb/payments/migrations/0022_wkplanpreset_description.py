# Generated by Django 2.2.8 on 2020-03-26 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0021_auto_20200326_1322"),
    ]

    operations = [
        migrations.AddField(
            model_name="wkplanpreset",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
    ]
