"""
AI-powered chat and insights API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.auth import get_current_user
from app.services.ai_service import process_nl_query, generate_insights
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None
    query_type: Optional[str] = None


class InsightResponse(BaseModel):
    category: str
    title: str
    description: str
    severity: str  # info, warning, success
    data: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process natural language queries about finances.

    Examples:
    - "How much did I spend on restaurants last month?"
    - "Show me my top 5 spending categories this year"
    - "Am I on track with my grocery budget?"
    """
    try:
        result = await process_nl_query(
            user_id=current_user["id"],
            query=message.message
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/insights", response_model=List[InsightResponse])
async def get_insights(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-generated financial insights.

    Returns:
    - Spending anomalies
    - Budget warnings
    - Savings opportunities
    - Trend analysis
    """
    try:
        insights = await generate_insights(user_id=current_user["id"])
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating insights: {str(e)}"
        )


@router.post("/categorize-suggestion")
async def suggest_category(
    transaction_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI suggestion for a specific transaction's category."""
    # TODO: Implement single transaction categorization
    raise HTTPException(
        status_code=501,
        detail="Category suggestion not yet implemented"
    )
