"""
Sync job model - Track processing jobs (file uploads, syncs, etc.).
"""

from tortoise import fields
from tortoise.models import Model


class SyncJob(Model):
    """Processing job tracking model."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="sync_jobs", on_delete=fields.CASCADE
    )

    job_type = fields.CharField(max_length=50)
    prefect_flow_run_id = fields.CharField(max_length=255, null=True)

    status = fields.CharField(max_length=50)
    stage = fields.CharField(max_length=50, null=True)
    progress = fields.JSONField(null=True)

    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)

    error_message = fields.TextField(null=True)
    meta = fields.JSONField(default=dict)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "sync_jobs"

    def __str__(self):
        return f"<SyncJob(id={self.id}, type={self.job_type}, status={self.status})>"
