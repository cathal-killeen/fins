"""
Categorization rules model - AI learned patterns.
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class CategorizationRule(Base):
    """AI categorization rules model."""

    __tablename__ = "categorization_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    pattern_type = Column(
        String(50), nullable=False
    )  # merchant_exact, merchant_contains, description_pattern
    pattern_value = Column(String, nullable=False)

    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))

    confidence_score = Column(Float, default=1.0)
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="categorization_rules")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            "user_id", "pattern_type", "pattern_value", name="uq_user_pattern"
        ),
    )

    def __repr__(self):
        return f"<CategorizationRule(id={self.id}, pattern={self.pattern_value}, category={self.category})>"
