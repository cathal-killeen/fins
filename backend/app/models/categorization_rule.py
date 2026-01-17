"""
Categorization rules model - AI learned patterns.
"""

from tortoise import fields
from tortoise.models import Model


class CategorizationRule(Model):
    """AI categorization rules model."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="categorization_rules", on_delete=fields.CASCADE
    )

    pattern_type = fields.CharField(max_length=50)
    pattern_value = fields.TextField()

    category = fields.CharField(max_length=100)
    subcategory = fields.CharField(max_length=100, null=True)

    confidence_score = fields.FloatField(default=1.0)
    usage_count = fields.IntField(default=0)
    last_used_at = fields.DatetimeField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "categorization_rules"
        unique_together = (("user", "pattern_type", "pattern_value"),)

    def __str__(self):
        return f"<CategorizationRule(id={self.id}, pattern={self.pattern_value}, category={self.category})>"
