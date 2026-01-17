"""
Account model - Bank accounts, credit cards, investments.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Account(Base):
    """Bank account model."""

    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    account_type = Column(
        String(50), nullable=False
    )  # checking, savings, credit_card, investment, cash
    institution = Column(String(255))
    account_name = Column(String(255), nullable=False)
    account_number_last4 = Column(String(4))
    currency = Column(String(3), default="USD")

    current_balance = Column(Numeric(15, 2))
    available_balance = Column(Numeric(15, 2))
    credit_limit = Column(Numeric(15, 2))  # For credit cards

    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(DateTime)
    sync_error = Column(Text)

    meta = Column(JSONB, default=dict)  # renamed from 'metadata' (reserved)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Account(id={self.id}, name={self.account_name}, type={self.account_type})>"
