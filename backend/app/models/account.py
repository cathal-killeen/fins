"""
Account model - Bank accounts, credit cards, investments.
"""

from tortoise import fields
from tortoise.models import Model


class Account(Model):
    """Bank account model."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="accounts", on_delete=fields.CASCADE
    )

    account_type = fields.CharField(max_length=50)  # checking, savings, credit_card
    institution = fields.CharField(max_length=255, null=True)
    account_name = fields.CharField(max_length=255)
    account_number_last4 = fields.CharField(max_length=4, null=True)
    currency = fields.CharField(max_length=3, default="USD")

    current_balance = fields.DecimalField(max_digits=15, decimal_places=2, null=True)
    available_balance = fields.DecimalField(max_digits=15, decimal_places=2, null=True)
    credit_limit = fields.DecimalField(max_digits=15, decimal_places=2, null=True)

    is_active = fields.BooleanField(default=True)
    last_synced_at = fields.DatetimeField(null=True)
    sync_error = fields.TextField(null=True)

    meta = fields.JSONField(default=dict)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    transactions: fields.ReverseRelation["Transaction"]

    class Meta:
        table = "accounts"

    def __str__(self):
        return f"<Account(id={self.id}, name={self.account_name}, type={self.account_type})>"
