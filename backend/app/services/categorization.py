"""
Transaction categorization service.
"""

from typing import List, Dict, Any, Optional


async def check_categorization_rules(
    merchant_name: Optional[str], description: str
) -> Optional[Dict[str, Any]]:
    """
    Check if there's a learned categorization rule for this transaction.

    Returns:
        Rule dict with category, subcategory, and confidence_score, or None
    """
    # TODO: Implement database query for categorization rules
    # Query by merchant_name (exact match) or description (pattern match)
    return None


async def update_transaction_category(
    transaction_id: str,
    category: str,
    subcategory: Optional[str],
    confidence: float,
    ai_categorized: bool,
):
    """Update a transaction's category."""
    # TODO: Implement database update
    pass


async def create_categorization_rule(result: Dict[str, Any]):
    """
    Create a new categorization rule from a high-confidence AI result.

    Args:
        result: Dict with transaction details and categorization
    """
    # TODO: Implement rule creation
    # Extract merchant name or description pattern
    # Store rule for future use
    pass


async def get_uncategorized_transactions(limit: int = 500) -> List[Dict[str, Any]]:
    """Get transactions that haven't been categorized yet."""
    # TODO: Implement database query
    return []
