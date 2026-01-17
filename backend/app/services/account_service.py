"""
Account service - Database operations for accounts.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.account import Account


class AccountService:
    """Service for account-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all accounts for a user.

        Returns:
            List of account dictionaries
        """
        accounts = (
            self.db.query(Account)
            .filter(Account.user_id == user_id)
            .filter(Account.is_active)
            .order_by(Account.created_at.desc())
            .all()
        )

        return [self._account_to_dict(account) for account in accounts]

    def get_account_by_id(
        self, account_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get an account by ID.

        Args:
            account_id: Account ID
            user_id: User ID (for security check)

        Returns:
            Account dictionary or None
        """
        account = (
            self.db.query(Account)
            .filter(Account.id == account_id)
            .filter(Account.user_id == user_id)
            .first()
        )

        return self._account_to_dict(account) if account else None

    def find_matching_accounts(
        self,
        user_id: str,
        institution: Optional[str] = None,
        account_type: Optional[str] = None,
        account_number_last4: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find accounts matching the given criteria.

        Args:
            user_id: User ID
            institution: Bank/institution name
            account_type: Account type (checking, savings, etc.)
            account_number_last4: Last 4 digits of account number

        Returns:
            List of matching accounts, ordered by match quality
        """
        query = (
            self.db.query(Account)
            .filter(Account.user_id == user_id)
            .filter(Account.is_active)
        )

        # Exact match on all criteria (best match)
        if institution and account_type and account_number_last4:
            exact_matches = (
                query.filter(Account.institution.ilike(f"%{institution}%"))
                .filter(Account.account_type == account_type)
                .filter(Account.account_number_last4 == account_number_last4)
                .all()
            )
            if exact_matches:
                return [self._account_to_dict(acc) for acc in exact_matches]

        # Strong match: institution + account_type
        if institution and account_type:
            strong_matches = (
                query.filter(Account.institution.ilike(f"%{institution}%"))
                .filter(Account.account_type == account_type)
                .all()
            )
            if strong_matches:
                return [self._account_to_dict(acc) for acc in strong_matches]

        # Medium match: institution + last4
        if institution and account_number_last4:
            medium_matches = (
                query.filter(Account.institution.ilike(f"%{institution}%"))
                .filter(Account.account_number_last4 == account_number_last4)
                .all()
            )
            if medium_matches:
                return [self._account_to_dict(acc) for acc in medium_matches]

        # Weak match: just institution
        if institution:
            weak_matches = query.filter(
                Account.institution.ilike(f"%{institution}%")
            ).all()
            if weak_matches:
                return [self._account_to_dict(acc) for acc in weak_matches]

        # Very weak match: just account_type
        if account_type:
            type_matches = query.filter(Account.account_type == account_type).all()
            if type_matches:
                return [self._account_to_dict(acc) for acc in type_matches]

        return []

    def create_account(
        self, user_id: str, account_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new account.

        Args:
            user_id: User ID
            account_data: Account data dictionary

        Returns:
            Created account dictionary
        """
        account = Account(
            user_id=user_id,
            account_name=account_data.get("account_name"),
            account_type=account_data.get("account_type", "unknown"),
            institution=account_data.get("institution"),
            account_number_last4=account_data.get("account_number_last4"),
            currency=account_data.get("currency", "USD"),
            current_balance=account_data.get("current_balance"),
            is_active=account_data.get("is_active", True),
            meta=account_data.get("meta", {}),
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        return self._account_to_dict(account)

    def update_account(
        self, account_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an account.

        Args:
            account_id: Account ID
            user_id: User ID (for security check)
            updates: Dictionary of fields to update

        Returns:
            Updated account dictionary or None
        """
        account = (
            self.db.query(Account)
            .filter(Account.id == account_id)
            .filter(Account.user_id == user_id)
            .first()
        )

        if not account:
            return None

        # Update allowed fields
        allowed_fields = [
            "account_name",
            "institution",
            "account_type",
            "account_number_last4",
            "current_balance",
            "available_balance",
            "credit_limit",
            "is_active",
            "last_synced_at",
            "sync_error",
            "meta",
        ]

        for field, value in updates.items():
            if field in allowed_fields and hasattr(account, field):
                setattr(account, field, value)

        account.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(account)

        return self._account_to_dict(account)

    def _account_to_dict(self, account: Account) -> Dict[str, Any]:
        """Convert Account model to dictionary."""
        return {
            "id": str(account.id),
            "user_id": str(account.user_id),
            "account_name": account.account_name,
            "account_type": account.account_type,
            "institution": account.institution,
            "account_number_last4": account.account_number_last4,
            "currency": account.currency,
            "current_balance": float(account.current_balance)
            if account.current_balance
            else None,
            "available_balance": float(account.available_balance)
            if account.available_balance
            else None,
            "credit_limit": float(account.credit_limit)
            if account.credit_limit
            else None,
            "is_active": account.is_active,
            "last_synced_at": account.last_synced_at.isoformat()
            if account.last_synced_at
            else None,
            "sync_error": account.sync_error,
            "meta": account.meta,
            "created_at": account.created_at.isoformat()
            if account.created_at
            else None,
            "updated_at": account.updated_at.isoformat()
            if account.updated_at
            else None,
        }
