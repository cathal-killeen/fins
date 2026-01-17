"""
Transaction service - Database operations for transactions.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.transaction import Transaction
from app.models.account import Account


class TransactionService:
    """Service for transaction-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def check_duplicates(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check for duplicate transactions.

        A transaction is considered a duplicate if it matches on:
        - Same account
        - Same date (within 1 day)
        - Same amount (exact match)
        - Similar merchant/description

        Args:
            account_id: Account ID
            transactions: List of transaction dictionaries to check

        Returns:
            {
                'duplicates': [...],  # Transactions that are duplicates
                'new': [...]          # Transactions that are new
            }
        """
        if not transactions:
            return {"duplicates": [], "new": []}

        duplicates = []
        new_transactions = []

        for txn in transactions:
            if self._is_duplicate(account_id, txn):
                duplicates.append(txn)
            else:
                new_transactions.append(txn)

        return {"duplicates": duplicates, "new": new_transactions}

    def _is_duplicate(self, account_id: str, txn: Dict[str, Any]) -> bool:
        """
        Check if a single transaction is a duplicate.

        Args:
            account_id: Account ID
            txn: Transaction dictionary with 'date', 'amount', 'description', 'merchant_name'

        Returns:
            True if duplicate exists, False otherwise
        """
        txn_date = txn.get("date")
        if isinstance(txn_date, str):
            txn_date = datetime.strptime(txn_date, "%Y-%m-%d").date()

        amount = Decimal(str(txn.get("amount", 0)))
        description = txn.get("description", "").lower()
        merchant_name = txn.get("merchant_name", "").lower()

        # Check for existing transaction with same account, date (±1 day), and amount
        date_from = txn_date - timedelta(days=1)
        date_to = txn_date + timedelta(days=1)

        existing = (
            self.db.query(Transaction)
            .filter(Transaction.account_id == account_id)
            .filter(Transaction.transaction_date >= date_from)
            .filter(Transaction.transaction_date <= date_to)
            .filter(Transaction.amount == amount)
            .all()
        )

        # Check if any existing transaction has similar description/merchant
        for existing_txn in existing:
            # Exact match on description or merchant is a duplicate
            if existing_txn.description.lower() == description or (
                merchant_name
                and existing_txn.merchant_name
                and existing_txn.merchant_name.lower() == merchant_name
            ):
                return True

            # Very similar description (contains each other) is likely a duplicate
            if (
                description in existing_txn.description.lower()
                or existing_txn.description.lower() in description
            ):
                return True

        return False

    def save_transactions(
        self, account_id: str, user_id: str, transactions: List[Dict[str, Any]]
    ) -> int:
        """
        Save transactions to database.

        Args:
            account_id: Account ID
            user_id: User ID
            transactions: List of transaction dictionaries

        Returns:
            Number of transactions saved
        """
        if not transactions:
            return 0

        saved_count = 0

        for txn_data in transactions:
            txn_date = txn_data.get("date")
            if isinstance(txn_date, str):
                txn_date = datetime.strptime(txn_date, "%Y-%m-%d").date()

            transaction = Transaction(
                account_id=account_id,
                user_id=user_id,
                transaction_date=txn_date,
                amount=Decimal(str(txn_data.get("amount", 0))),
                currency=txn_data.get("currency", "USD"),
                description=txn_data.get("description", ""),
                merchant_name=txn_data.get("merchant_name"),
                category=txn_data.get("category"),
                subcategory=txn_data.get("subcategory"),
                tags=txn_data.get("tags", []),
                confidence_score=txn_data.get("confidence"),
                ai_categorized=txn_data.get("category") is not None,
                user_verified=False,
                notes=txn_data.get("notes"),
                meta=txn_data.get("meta", {}),
            )

            self.db.add(transaction)
            saved_count += 1

        # Commit all transactions at once
        self.db.commit()

        return saved_count

    def get_user_transactions(
        self,
        user_id: str,
        account_id: Optional[str] = None,
        since: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get user's transactions.

        Args:
            user_id: User ID
            account_id: Optional account ID filter
            since: Optional date filter (transactions after this date)
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dictionaries
        """
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        if account_id:
            query = query.filter(Transaction.account_id == account_id)

        if since:
            query = query.filter(Transaction.transaction_date >= since)

        transactions = (
            query.order_by(Transaction.transaction_date.desc()).limit(limit).all()
        )

        return [self._transaction_to_dict(txn) for txn in transactions]

    def _transaction_to_dict(self, txn: Transaction) -> Dict[str, Any]:
        """Convert Transaction model to dictionary."""
        return {
            "id": str(txn.id),
            "account_id": str(txn.account_id),
            "user_id": str(txn.user_id),
            "transaction_date": txn.transaction_date.isoformat()
            if txn.transaction_date
            else None,
            "post_date": txn.post_date.isoformat() if txn.post_date else None,
            "amount": float(txn.amount) if txn.amount else 0,
            "currency": txn.currency,
            "description": txn.description,
            "merchant_name": txn.merchant_name,
            "category": txn.category,
            "subcategory": txn.subcategory,
            "tags": txn.tags or [],
            "is_recurring": txn.is_recurring,
            "recurring_group_id": str(txn.recurring_group_id)
            if txn.recurring_group_id
            else None,
            "confidence_score": txn.confidence_score,
            "ai_categorized": txn.ai_categorized,
            "user_verified": txn.user_verified,
            "notes": txn.notes,
            "meta": txn.meta or {},
            "created_at": txn.created_at.isoformat() if txn.created_at else None,
            "updated_at": txn.updated_at.isoformat() if txn.updated_at else None,
        }
