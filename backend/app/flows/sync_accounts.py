"""
Daily account synchronization workflow.
"""

from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta
from typing import List, Dict, Any
import asyncio


@task(
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
async def sync_single_account(account_id: str) -> Dict[str, Any]:
    """
    Sync a single account with retry logic.
    Returns: {'account_id': str, 'new_transactions': int, 'success': bool}
    """
    # TODO: Implement bank API sync logic (e.g., Plaid integration)
    # This is a placeholder for actual implementation
    print(f"Syncing account {account_id}")

    # Placeholder return
    return {"account_id": account_id, "new_transactions": 0, "success": True}


@task
async def deduplicate_transactions(user_id: str, account_id: str):
    """Remove duplicate transactions based on amount, date, and merchant"""
    from app.services.import_service import remove_duplicates

    print(f"Deduplicating transactions for account {account_id}")
    removed_count = await remove_duplicates(user_id, account_id)
    print(f"Removed {removed_count} duplicate transactions")

    return removed_count


@task
async def queue_for_categorization(transaction_ids: List[str]):
    """Queue uncategorized transactions for AI processing"""
    print(f"Queued {len(transaction_ids)} transactions for categorization")
    # The categorization flow will pick these up
    return len(transaction_ids)


async def get_user_accounts(user_id: str) -> List[Dict[str, Any]]:
    """Get all active accounts for a user"""
    # TODO: Implement database query
    return []


async def get_all_active_accounts() -> List[Dict[str, Any]]:
    """Get all active accounts in the system"""
    # TODO: Implement database query
    return []


async def get_uncategorized_transactions() -> List[Dict[str, Any]]:
    """Get all uncategorized transactions"""
    # TODO: Implement database query
    return []


@flow(name="daily-account-sync", log_prints=True)
async def daily_account_sync_flow(user_id: str = None):
    """
    Main sync flow - runs daily for all users or on-demand for specific user.
    """
    # Get accounts to sync
    if user_id:
        accounts = await get_user_accounts(user_id)
    else:
        accounts = await get_all_active_accounts()

    print(f"Starting sync for {len(accounts)} accounts")

    if not accounts:
        print("No accounts to sync")
        return {"total_accounts": 0, "successful_syncs": 0, "new_transactions": 0}

    # Sync all accounts in parallel
    sync_results = await sync_single_account.map(
        [account["id"] for account in accounts]
    )

    # Deduplicate transactions for each account
    await deduplicate_transactions.map(
        [(account["user_id"], account["id"]) for account in accounts]
    )

    # Get all new uncategorized transactions
    uncategorized = await get_uncategorized_transactions()

    if uncategorized:
        print(f"Found {len(uncategorized)} uncategorized transactions")
        await queue_for_categorization([t["id"] for t in uncategorized])

    # Log summary
    total_new = sum(r["new_transactions"] for r in sync_results if r["success"])
    print(f"✅ Sync complete: {total_new} new transactions")

    return {
        "total_accounts": len(accounts),
        "successful_syncs": sum(1 for r in sync_results if r["success"]),
        "new_transactions": total_new,
    }
