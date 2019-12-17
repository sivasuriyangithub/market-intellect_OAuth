# Generated by Django 2.2.8 on 2019-12-14 01:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("users", "0005_auto_20191214_0117")]

    operations = [
        migrations.AddField(
            model_name="organizationcredentials",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]