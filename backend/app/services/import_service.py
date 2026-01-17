"""
Transaction import service for CSV/OFX files.
"""

from typing import List, Dict, Any
import csv
import io


async def remove_duplicates(user_id: str, account_id: str) -> int:
    """
    Remove duplicate transactions based on amount, date, and merchant.

    Returns:
        Number of duplicates removed
    """
    # TODO: Implement duplicate detection
    # Algorithm:
    # 1. Find transactions with same amount, date, and merchant
    # 2. Keep the oldest one
    # 3. Delete duplicates
    return 0


async def parse_csv(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Parse CSV file and extract transactions.

    Supports common CSV formats from banks.
    """
    # TODO: Implement CSV parsing
    # Handle different CSV formats:
    # - Date formats
    # - Amount formats (positive/negative)
    # - Column name variations

    content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    transactions = []
    for row in reader:
        # This is a basic example - needs to be more robust
        transaction = {
            "date": row.get("Date") or row.get("date"),
            "amount": row.get("Amount") or row.get("amount"),
            "description": row.get("Description") or row.get("description"),
            "merchant": row.get("Merchant") or row.get("merchant"),
        }
        transactions.append(transaction)

    return transactions


async def import_transactions(
    user_id: str, account_id: str, transactions: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Import transactions into the database.

    Returns:
        Dict with counts of imported, skipped, and failed transactions
    """
    # TODO: Implement transaction import
    # 1. Validate each transaction
    # 2. Check for duplicates
    # 3. Insert into database
    # 4. Return statistics

    return {"imported": 0, "skipped": 0, "failed": 0}
