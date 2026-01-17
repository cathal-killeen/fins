"""
Admin model for FastAPI-Admin.
"""

from fastapi_admin.models import AbstractAdmin
from tortoise import fields


class Admin(AbstractAdmin):
    """Admin user model for the admin panel."""

    username = fields.CharField(max_length=50, unique=True, index=True)
    password = fields.CharField(max_length=255)

    class Meta:
        table = "admin_users"

    def __str__(self) -> str:
        return f"<Admin(username={self.username})>"
