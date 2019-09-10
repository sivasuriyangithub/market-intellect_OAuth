# Generated by Django 2.2.3 on 2019-09-10 01:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("payments", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="billingaccountmember",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="organization_users",
                to="payments.BillingAccount",
                verbose_name="billing account",
            ),
        ),
        migrations.AlterField(
            model_name="billingaccountowner",
            name="organization",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owner",
                to="payments.BillingAccount",
                verbose_name="billing account",
            ),
        ),
        migrations.AlterField(
            model_name="billingaccountowner",
            name="organization_user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="payments.BillingAccountMember",
                verbose_name="billing account member",
            ),
        ),
    ]