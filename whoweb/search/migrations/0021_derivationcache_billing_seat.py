# Generated by Django 2.2.8 on 2020-03-13 18:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0015_wkplanpreset"),
        ("search", "0020_auto_20200313_1100"),
    ]

    operations = [
        migrations.AddField(
            model_name="derivationcache",
            name="billing_seat",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="payments.BillingAccountMember",
            ),
        ),
    ]
