"""
Budget model.
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Numeric,
    Date,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Budget(Base):
    """Budget model."""

    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))

    amount = Column(Numeric(15, 2), nullable=False)
    period = Column(String(20), nullable=False)  # monthly, quarterly, yearly

    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    rollover_enabled = Column(Boolean, default=False)
    alert_threshold = Column(Float, default=0.8)  # Alert at 80%

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="budgets")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "category",
            "subcategory",
            "period",
            "start_date",
            name="uq_user_budget",
        ),
    )

    def __repr__(self):
        return f"<Budget(id={self.id}, category={self.category}, amount={self.amount}, period={self.period})>"
