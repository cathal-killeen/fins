"""
AI-powered transaction categorization workflow.
"""

from prefect import flow, task
import json
from typing import List, Dict, Any


@task(retries=2, retry_delay_seconds=30)
async def categorize_batch(
    transaction_batch: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Categorize a batch of transactions using LLM.
    Batch size: 20-50 transactions for cost efficiency.
    """
    from app.services.categorization import (
        check_categorization_rules,
    )
    from app.services.ai_service import llm_service

    # Check for learned patterns first
    categorized_by_rules = []
    needs_ai = []

    for txn in transaction_batch:
        rule = await check_categorization_rules(
            txn.get("merchant_name"), txn.get("description")
        )
        if rule and rule.get("confidence_score", 0) > 0.8:
            categorized_by_rules.append(
                {
                    "id": txn["id"],
                    "category": rule["category"],
                    "subcategory": rule.get("subcategory"),
                    "confidence": rule["confidence_score"],
                    "method": "rule",
                }
            )
        else:
            needs_ai.append(txn)

    # AI categorize remaining transactions
    ai_results = []
    if needs_ai:
        prompt = build_categorization_prompt(needs_ai)

        messages = [{"role": "user", "content": prompt}]
        response = await llm_service.complete(messages, max_tokens=4096)

        ai_results = json.loads(response)

    return categorized_by_rules + ai_results


@task
async def save_categorizations(categorization_results: List[Dict[str, Any]]):
    """Save categorization results to database"""
    from app.services.categorization import (
        update_transaction_category,
        create_categorization_rule,
    )

    for result in categorization_results:
        await update_transaction_category(
            transaction_id=result["id"],
            category=result["category"],
            subcategory=result.get("subcategory"),
            confidence=result["confidence"],
            ai_categorized=(result.get("method") == "ai"),
        )

        # Learn from high-confidence AI categorizations
        if result.get("method") == "ai" and result["confidence"] > 0.9:
            await create_categorization_rule(result)


def build_categorization_prompt(transactions: List[Dict[str, Any]]) -> str:
    """
    Build prompt for batch transaction categorization.
    """

    categories = {
        "Income": ["Salary", "Freelance", "Investment Income", "Gifts", "Refunds"],
        "Housing": [
            "Rent/Mortgage",
            "Utilities",
            "Internet",
            "Home Maintenance",
            "Furniture",
        ],
        "Transportation": [
            "Gas",
            "Public Transit",
            "Ride Share",
            "Car Maintenance",
            "Parking",
        ],
        "Food": ["Groceries", "Restaurants", "Coffee Shops", "Fast Food", "Delivery"],
        "Shopping": ["Clothing", "Electronics", "Home Goods", "Personal Care", "Books"],
        "Entertainment": [
            "Streaming Services",
            "Movies",
            "Gaming",
            "Hobbies",
            "Events",
        ],
        "Healthcare": ["Medical", "Dental", "Pharmacy", "Health Insurance", "Fitness"],
        "Financial": ["Bank Fees", "Interest", "Investments", "Insurance", "Taxes"],
        "Personal": ["Haircut", "Spa", "Subscriptions", "Gifts", "Education"],
        "Travel": ["Flights", "Hotels", "Vacation", "Travel Insurance"],
        "Other": ["Uncategorized"],
    }

    prompt = f"""You are a financial transaction categorization expert. Analyze these transactions and categorize each one.

Available categories and subcategories:
{json.dumps(categories, indent=2)}

Transactions to categorize:
{json.dumps(transactions, indent=2)}

For each transaction, determine:
1. The most appropriate category and subcategory
2. Whether it appears to be a recurring transaction (subscription, bill, etc.)
3. Your confidence level (0.0 to 1.0)

Return ONLY a JSON array with this structure:
[
  {{
    "id": "transaction_id",
    "category": "category_name",
    "subcategory": "subcategory_name",
    "is_recurring": true/false,
    "confidence": 0.95,
    "reasoning": "brief explanation"
  }}
]

Guidelines:
- Use merchant name as primary signal
- Consider transaction amount patterns
- Look for subscription keywords (monthly, annual, membership)
- Be conservative with confidence scores
- If truly unclear, use confidence < 0.5 and suggest "Other"
"""

    return prompt


@flow(name="ai-categorization", log_prints=True)
async def categorization_flow():
    """
    Categorize uncategorized transactions in batches.
    """
    from app.services.categorization import get_uncategorized_transactions

    uncategorized = await get_uncategorized_transactions(limit=500)

    if not uncategorized:
        print("No transactions to categorize")
        return

    print(f"Categorizing {len(uncategorized)} transactions")

    # Process in batches of 30
    batch_size = 30
    batches = [
        uncategorized[i : i + batch_size]
        for i in range(0, len(uncategorized), batch_size)
    ]

    # Process batches in parallel (with rate limiting)
    results = await categorize_batch.map(batches)

    # Flatten results and save
    all_results = [item for batch in results for item in batch]
    await save_categorizations(all_results)

    print(f"✅ Categorized {len(all_results)} transactions")

    return {"total_categorized": len(all_results), "batches_processed": len(batches)}
