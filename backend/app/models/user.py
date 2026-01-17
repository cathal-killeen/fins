"""
User model.
"""

from tortoise import fields
from tortoise.models import Model


class User(Model):
    """User account model."""

    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    accounts: fields.ReverseRelation["Account"]
    transactions: fields.ReverseRelation["Transaction"]
    categorization_rules: fields.ReverseRelation["CategorizationRule"]
    budgets: fields.ReverseRelation["Budget"]
    sync_jobs: fields.ReverseRelation["SyncJob"]

    class Meta:
        table = "users"

    def __str__(self):
        return f"<User(id={self.id}, email={self.email})>"
