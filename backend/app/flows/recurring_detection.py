"""
Recurring transaction detection workflow.
"""

from prefect import flow, task
from datetime import datetime, timedelta
from typing import List, Dict, Any


@task
async def detect_recurring_transactions(user_id: str) -> List[Dict[str, Any]]:
    """
    Detect recurring transactions (subscriptions, bills).
    Algorithm: Find transactions with similar amounts and regular intervals.
    """
    from app.services.analytics_service import find_recurring_patterns

    # Get transactions from last 6 months
    six_months_ago = datetime.now() - timedelta(days=180)
    print(f"Detecting recurring patterns for user {user_id} since {six_months_ago}")

    # TODO: Implement actual pattern detection
    recurring_groups = await find_recurring_patterns(user_id, six_months_ago)

    return recurring_groups


@task
async def mark_as_recurring(recurring_groups: List[Dict[str, Any]]):
    """Mark transactions as recurring and create recurring groups"""
    from app.services.analytics_service import (
        create_recurring_group,
        mark_transactions_recurring,
    )

    for group in recurring_groups:
        group_id = await create_recurring_group(group)
        await mark_transactions_recurring(group["transaction_ids"], group_id)
        print(
            f"Created recurring group {group_id} with {len(group['transaction_ids'])} transactions"
        )

    return len(recurring_groups)


async def get_all_users() -> List[Dict[str, Any]]:
    """Get all users in the system"""
    # TODO: Implement database query
    return []


@flow(name="recurring-detection", log_prints=True)
async def recurring_detection_flow():
    """
    Detect and mark recurring transactions.
    Runs weekly.
    """
    users = await get_all_users()

    if not users:
        print("No users to process")
        return {"total_users": 0, "recurring_patterns_found": 0}

    total_patterns = 0

    for user in users:
        recurring = await detect_recurring_transactions(user["id"])
        if recurring:
            count = await mark_as_recurring(recurring)
            total_patterns += count
            print(f"Found {count} recurring patterns for user {user['id']}")

    print(f"✅ Detected {total_patterns} total recurring patterns")

    return {"total_users": len(users), "recurring_patterns_found": total_patterns}
