# Generated by Django 2.2.8 on 2020-02-06 00:02

from django.db import migrations, models
import whoweb.contrib.fields


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_auto_20191217_0651"),
    ]

    operations = [
        migrations.AlterModelOptions(name="user", options={},),
        migrations.AddField(
            model_name="developerkey",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                null=True,
                verbose_name="ID",
            ),
        ),
        migrations.AddField(
            model_name="group",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                null=True,
                verbose_name="ID",
            ),
        ),
        migrations.AddField(
            model_name="seat",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                null=True,
                verbose_name="ID",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="public_id",
            field=models.CharField(
                default=whoweb.contrib.fields.random_public_id,
                editable=False,
                max_length=16,
                null=True,
                verbose_name="ID",
            ),
        ),
        migrations.AlterField(
            model_name="developerkey",
            name="id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="group",
            name="id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="seat",
            name="id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]