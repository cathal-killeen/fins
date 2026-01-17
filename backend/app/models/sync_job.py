"""
Sync job model - Track processing jobs (file uploads, syncs, etc.).
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class SyncJob(Base):
    """Processing job tracking model."""

    __tablename__ = "sync_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_type = Column(
        String(50), nullable=False
    )  # account_sync, categorization, analytics, file_upload
    prefect_flow_run_id = Column(String(255))

    status = Column(
        String(50), nullable=False
    )  # pending, running, completed, failed, awaiting_confirmation
    stage = Column(String(50))  # current processing stage
    progress = Column(JSONB)  # progress information (percentage, message, etc.)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    error_message = Column(Text)
    meta = Column(JSONB, default=dict)  # renamed from 'metadata' (reserved)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sync_jobs")

    def __repr__(self):
        return f"<SyncJob(id={self.id}, type={self.job_type}, status={self.status})>"
