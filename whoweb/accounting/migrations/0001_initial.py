# Generated by Django 2.2.6 on 2019-12-04 02:14

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid
import whoweb.accounting.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ledger",
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
                        help_text="Name of this ledger", max_length=255, unique=True
                    ),
                ),
                ("liability", models.BooleanField(default=False)),
                ("account_code", models.IntegerField(unique=True)),
                (
                    "description",
                    models.TextField(blank=True, help_text="Purpose of this ledger."),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="LedgerEntry",
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
                    "entry_id",
                    models.UUIDField(
                        default=uuid.uuid4, help_text="UUID for this ledger entry"
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=4,
                        help_text="Amount for this entry.Debits are positive, and credits are negative.",
                        max_digits=24,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "ledger",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="entries",
                        to="accounting.Ledger",
                    ),
                ),
            ],
            options={"verbose_name_plural": "ledger entries"},
        ),
        migrations.CreateModel(
            name="TransactionKind",
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
                        help_text="Name of this transaction type",
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Any notes to go along with this Transaction.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Transaction",
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
                    "transaction_id",
                    models.UUIDField(
                        default=uuid.uuid4, help_text="UUID for this transaction"
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        help_text="Any notes to go along with this Transaction.",
                    ),
                ),
                (
                    "posted_timestamp",
                    models.DateTimeField(
                        db_index=True,
                        help_text="Time the transaction was posted.  Change this field to model retroactive ledger entries.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "kind",
                    models.ForeignKey(
                        default=whoweb.accounting.models.get_or_create_manual_transaction_kind_id,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounting.TransactionKind",
                    ),
                ),
                (
                    "ledgers",
                    models.ManyToManyField(
                        through="accounting.LedgerEntry", to="accounting.Ledger"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="transaction",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="entries",
                to="accounting.Transaction",
            ),
        ),
        migrations.CreateModel(
            name="TransactionRelatedObject",
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
                ("related_object_id", models.PositiveIntegerField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "related_object_content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="contenttypes.ContentType",
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="related_objects",
                        to="accounting.Transaction",
                    ),
                ),
            ],
            options={
                "unique_together": {
                    ("transaction", "related_object_content_type", "related_object_id")
                }
            },
        ),
        migrations.CreateModel(
            name="LedgerBalance",
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
                ("related_object_id", models.PositiveIntegerField(db_index=True)),
                (
                    "balance",
                    models.DecimalField(
                        decimal_places=4, default=Decimal("0"), max_digits=24
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "ledger",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounting.Ledger",
                    ),
                ),
                (
                    "related_object_content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="contenttypes.ContentType",
                    ),
                ),
            ],
            options={
                "unique_together": {
                    ("ledger", "related_object_content_type", "related_object_id")
                }
            },
        ),
    ]
