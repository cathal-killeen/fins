"""
Accounts API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

router = APIRouter()


class AccountCreate(BaseModel):
    account_type: str
    account_name: str
    institution: Optional[str] = None
    account_number_last4: Optional[str] = None
    currency: str = "USD"
    current_balance: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    current_balance: Optional[Decimal] = None
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: str
    user_id: str
    account_type: str
    account_name: str
    institution: Optional[str]
    account_number_last4: Optional[str]
    currency: str
    current_balance: Optional[Decimal]
    available_balance: Optional[Decimal]
    credit_limit: Optional[Decimal]
    is_active: bool
    last_synced_at: Optional[datetime]
    created_at: datetime


@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """List all accounts for the current user."""
    # TODO: Implement account listing
    return []


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new account."""
    # TODO: Implement account creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account creation not yet implemented",
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific account by ID."""
    # TODO: Implement account retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
    )


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account: AccountUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an account."""
    # TODO: Implement account update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account update not yet implemented",
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an account."""
    # TODO: Implement account deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account deletion not yet implemented",
    )


@router.post("/{account_id}/sync")
async def sync_account(
    account_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger a manual sync for an account."""
    # TODO: Trigger Prefect flow for account sync
    return {"message": "Sync initiated", "account_id": account_id}
