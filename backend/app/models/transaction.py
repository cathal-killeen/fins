"""
Transaction model.
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Numeric,
    Text,
    Date,
    Float,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Transaction(Base):
    """Financial transaction model."""

    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_date = Column(Date, nullable=False, index=True)
    post_date = Column(Date)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")

    description = Column(Text, nullable=False)
    merchant_name = Column(String(255), index=True)

    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    tags = Column(ARRAY(Text), default=list)

    is_recurring = Column(Boolean, default=False)
    recurring_group_id = Column(UUID(as_uuid=True))

    confidence_score = Column(Float)  # AI confidence (0-1)
    ai_categorized = Column(Boolean, default=False)
    user_verified = Column(Boolean, default=False)

    notes = Column(Text)
    meta = Column(JSONB, default=dict)  # renamed from 'metadata' (reserved)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    account = relationship("Account", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_transactions_date_desc", transaction_date.desc()),
        Index("idx_transactions_account_date", account_id, transaction_date.desc()),
        Index("idx_transactions_user_date", user_id, transaction_date.desc()),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.transaction_date}, amount={self.amount}, merchant={self.merchant_name})>"
