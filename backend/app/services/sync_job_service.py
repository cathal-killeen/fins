"""
Sync job service - Database operations for job tracking.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.sync_job import SyncJob


class SyncJobService:
    """Service for sync job tracking operations."""

    async def create_job(
        self, user_id: str, job_id: str, job_type: str = "file_upload"
    ) -> Dict[str, Any]:
        """
        Create a new sync job.

        Args:
            user_id: User ID
            job_id: Unique job identifier
            job_type: Type of job (file_upload, account_sync, etc.)

        Returns:
            Created job dictionary
        """
        job = await SyncJob.create(
            id=uuid.UUID(job_id),
            user_id=user_id,
            job_type=job_type,
            status="pending",
            stage="uploading",
            progress={"percentage": 0, "message": "Initializing..."},
            started_at=datetime.utcnow(),
            meta={},
        )

        return self._job_to_dict(job)

    async def get_job(
        self, job_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a sync job by ID.

        Args:
            job_id: Job ID
            user_id: Optional user ID for security check

        Returns:
            Job dictionary or None
        """
        query = SyncJob.filter(id=job_id)

        if user_id:
            query = query.filter(user_id=user_id)

        job = await query.first()

        return self._job_to_dict(job) if job else None

    async def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a sync job.

        Args:
            job_id: Job ID
            status: Job status
            stage: Current stage
            progress: Progress information
            error_message: Error message if failed
            metadata: Additional metadata

        Returns:
            Updated job dictionary or None
        """
        job = await SyncJob.filter(id=job_id).first()

        if not job:
            return None

        if status:
            job.status = status

        if stage:
            job.stage = stage

        if progress:
            job.progress = progress

        if error_message:
            job.error_message = error_message

        if metadata:
            # Merge with existing metadata
            existing_meta = job.meta or {}
            existing_meta.update(metadata)
            job.meta = existing_meta

        # Mark as completed if status is completed or failed
        if status in ["completed", "failed"]:
            job.completed_at = datetime.utcnow()

        await job.save()

        return self._job_to_dict(job)

    def _job_to_dict(self, job: SyncJob) -> Dict[str, Any]:
        """Convert SyncJob model to dictionary."""
        return {
            "id": str(job.id),
            "user_id": str(job.user_id),
            "job_type": job.job_type,
            "prefect_flow_run_id": job.prefect_flow_run_id,
            "status": job.status,
            "stage": job.stage,
            "progress": job.progress or {},
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "metadata": job.meta or {},
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
