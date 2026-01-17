"""
Budget model.
"""

from tortoise import fields
from tortoise.models import Model


class Budget(Model):
    """Budget model."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="budgets", on_delete=fields.CASCADE
    )

    category = fields.CharField(max_length=100)
    subcategory = fields.CharField(max_length=100, null=True)

    amount = fields.DecimalField(max_digits=15, decimal_places=2)
    period = fields.CharField(max_length=20)  # monthly, quarterly, yearly

    start_date = fields.DateField()
    end_date = fields.DateField(null=True)

    rollover_enabled = fields.BooleanField(default=False)
    alert_threshold = fields.FloatField(default=0.8)  # Alert at 80%

    is_active = fields.BooleanField(default=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "budgets"
        unique_together = (("user", "category", "subcategory", "period", "start_date"),)

    def __str__(self):
        return f"<Budget(id={self.id}, category={self.category}, amount={self.amount}, period={self.period})>"
