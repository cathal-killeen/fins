"""
Transaction model.
"""

from tortoise import fields
from tortoise.models import Model


class Transaction(Model):
    """Financial transaction model."""

    id = fields.UUIDField(pk=True)
    account = fields.ForeignKeyField(
        "models.Account", related_name="transactions", on_delete=fields.CASCADE
    )
    user = fields.ForeignKeyField(
        "models.User", related_name="transactions", on_delete=fields.CASCADE
    )

    transaction_date = fields.DateField()
    post_date = fields.DateField(null=True)
    amount = fields.DecimalField(max_digits=15, decimal_places=2)
    currency = fields.CharField(max_length=3, default="USD")

    description = fields.TextField()
    merchant_name = fields.CharField(max_length=255, null=True)

    category = fields.CharField(max_length=100, null=True)
    subcategory = fields.CharField(max_length=100, null=True)
    tags = fields.JSONField(default=list)

    is_recurring = fields.BooleanField(default=False)
    recurring_group_id = fields.UUIDField(null=True)

    confidence_score = fields.FloatField(null=True)  # AI confidence (0-1)
    ai_categorized = fields.BooleanField(default=False)
    user_verified = fields.BooleanField(default=False)

    notes = fields.TextField(null=True)
    meta = fields.JSONField(default=dict)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "transactions"
        indexes = [
            ("transaction_date",),
            ("account", "transaction_date"),
            ("user", "transaction_date"),
        ]

    def __str__(self):
        return f"<Transaction(id={self.id}, date={self.transaction_date}, amount={self.amount}, merchant={self.merchant_name})>"
