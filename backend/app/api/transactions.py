"""
Transactions API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

router = APIRouter()


class TransactionCreate(BaseModel):
    account_id: str
    transaction_date: date
    amount: Decimal
    description: str
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    merchant_name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    user_id: str
    transaction_date: date
    amount: Decimal
    currency: str
    description: str
    merchant_name: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    tags: List[str]
    is_recurring: bool
    confidence_score: Optional[float]
    ai_categorized: bool
    user_verified: bool
    notes: Optional[str]
    created_at: datetime


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    account_id: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List transactions with optional filters."""
    # TODO: Implement transaction listing with filters
    return []


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction: TransactionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new transaction manually."""
    # TODO: Implement transaction creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Transaction creation not yet implemented",
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific transaction by ID."""
    # TODO: Implement transaction retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
    )


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction: TransactionUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a transaction (e.g., change category, add notes)."""
    # TODO: Implement transaction update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Transaction update not yet implemented",
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a transaction."""
    # TODO: Implement transaction deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Transaction deletion not yet implemented",
    )


@router.post("/import")
async def import_transactions(
    file: UploadFile = File(...),
    account_id: str = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Import transactions from a CSV file."""
    # TODO: Implement CSV import
    # 1. Validate file type
    # 2. Parse CSV
    # 3. Create transactions
    # 4. Trigger categorization flow
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Transaction import not yet implemented",
    )


@router.post("/categorize")
async def trigger_categorization(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """Trigger AI categorization for uncategorized transactions."""
    # TODO: Trigger Prefect categorization flow
    return {"message": "Categorization flow triggered"}
