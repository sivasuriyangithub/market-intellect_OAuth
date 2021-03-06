# Generated by Django 2.2.6 on 2019-11-06 00:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import organizations.base
import organizations.fields


class Migration(migrations.Migration):

    replaces = [
        ("payments", "0001_initial"),
        ("payments", "0002_auto_20190912_2355"),
        ("payments", "0003_auto_20190917_2353"),
        ("payments", "0004_auto_20191106_0014"),
    ]

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        ("organizations", "0003_field_fix_and_editable"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingAccount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="The name of the organization", max_length=200
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created",
                    organizations.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "modified",
                    organizations.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "slug",
                    organizations.fields.SlugField(
                        blank=True,
                        editable=False,
                        help_text="The name in all lowercase, suitable for URL identification",
                        max_length=200,
                        populate_from="name",
                        unique=True,
                    ),
                ),
                ("credit_pool", models.IntegerField(blank=True, default=0)),
                ("trial_credit_pool", models.IntegerField(blank=True, default=0)),
                (
                    "org",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="organizations.Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "billing account",
                "verbose_name_plural": "billing accounts",
            },
            bases=(organizations.base.UnicodeMixin, models.Model),
        ),
        migrations.CreateModel(
            name="BillingAccountMember",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    organizations.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "modified",
                    organizations.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("is_admin", models.BooleanField(default=False)),
                ("seat_credits", models.IntegerField(default=0)),
                ("seat_trial_credits", models.IntegerField(default=0)),
                ("pool_credits", models.BooleanField(default=False)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organization_users",
                        to="payments.BillingAccount",
                    ),
                ),
                (
                    "seat",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="billing",
                        to="users.Seat",
                        verbose_name="group seat",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments_billingaccountmember",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "billing account member",
                "verbose_name_plural": "billing account members",
            },
            bases=(organizations.base.UnicodeMixin, models.Model),
        ),
        migrations.CreateModel(
            name="BillingAccountOwner",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    organizations.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "modified",
                    organizations.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "organization",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="owner",
                        to="payments.BillingAccount",
                    ),
                ),
                (
                    "organization_user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="payments.BillingAccountMember",
                    ),
                ),
            ],
            options={
                "verbose_name": "billing account owner",
                "verbose_name_plural": "billing account owners",
            },
            bases=(organizations.base.UnicodeMixin, models.Model),
        ),
        migrations.AddField(
            model_name="billingaccount",
            name="seats",
            field=models.ManyToManyField(
                related_name="billing_account",
                through="payments.BillingAccountMember",
                to="users.Seat",
            ),
        ),
        migrations.AddField(
            model_name="billingaccount",
            name="users",
            field=models.ManyToManyField(
                related_name="payments_billingaccount",
                through="payments.BillingAccountMember",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveField(model_name="billingaccount", name="org"),
        migrations.AddField(
            model_name="billingaccount",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="users.Group",
            ),
        ),
        migrations.AlterField(
            model_name="billingaccount",
            name="slug",
            field=organizations.fields.SlugField(
                editable=True,
                help_text="The name in all lowercase, suitable for URL identification",
                max_length=200,
                populate_from="name",
                unique=True,
            ),
        ),
    ]
