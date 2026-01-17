"""
CSV parsing utilities for bank statements.
"""

import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


def detect_delimiter(file_path: str) -> str:
    """
    Detect the delimiter used in a CSV file (comma, semicolon, tab).
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        first_line = f.readline()

    # Count occurrences of common delimiters
    comma_count = first_line.count(",")
    semicolon_count = first_line.count(";")
    tab_count = first_line.count("\t")

    # Return the most common delimiter
    counts = {",": comma_count, ";": semicolon_count, "\t": tab_count}
    return max(counts, key=counts.get)


def parse_date(date_str: str) -> Optional[str]:
    """
    Parse various date formats and return YYYY-MM-DD.

    Supports formats:
    - MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
    - M/D/YY, D/M/YY
    - Month DD, YYYY
    """
    if not date_str or pd.isna(date_str):
        return None

    date_str = str(date_str).strip()

    # Try common date formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%m/%d/%y",
        "%d/%m/%y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y%m%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try pandas date parser as fallback
    try:
        dt = pd.to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, pd.errors.ParserError):
        return None


def parse_amount(amount_str: str) -> Optional[float]:
    """
    Parse amount string and return float.

    Handles:
    - Currency symbols ($, €, £)
    - Thousands separators (,)
    - Parentheses for negative amounts
    - CR/DR indicators
    """
    if not amount_str or pd.isna(amount_str):
        return None

    amount_str = str(amount_str).strip()

    # Check for credit/debit indicators
    is_negative = False
    if "DR" in amount_str.upper() or amount_str.startswith("("):
        is_negative = True

    # Remove currency symbols, commas, and other non-numeric chars
    clean_amount = re.sub(r"[^\d.-]", "", amount_str)

    try:
        amount = float(clean_amount)
        return -abs(amount) if is_negative else amount
    except ValueError:
        return None


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to standard format.
    """
    # Common column name mappings
    column_mappings = {
        # Date columns
        "date": "date",
        "transaction date": "date",
        "trans date": "date",
        "posting date": "date",
        "post date": "date",
        # Amount columns
        "amount": "amount",
        "debit": "amount",
        "credit": "amount",
        "transaction amount": "amount",
        # Description columns
        "description": "description",
        "desc": "description",
        "transaction description": "description",
        "memo": "description",
        "details": "description",
        # Merchant columns
        "merchant": "merchant_name",
        "payee": "merchant_name",
        "vendor": "merchant_name",
    }

    # Convert column names to lowercase and map
    df.columns = df.columns.str.lower().str.strip()
    df = df.rename(columns=column_mappings)

    return df


def detect_header_row(file_path: str, delimiter: str) -> int:
    """
    Detect which row contains the header.
    Returns the row index (0-based).
    """
    # Read first 10 rows
    df = pd.read_csv(file_path, delimiter=delimiter, nrows=10, header=None)

    # Look for common header keywords
    header_keywords = [
        "date",
        "amount",
        "description",
        "transaction",
        "debit",
        "credit",
    ]

    for idx, row in df.iterrows():
        row_str = " ".join(row.astype(str).str.lower())
        if any(keyword in row_str for keyword in header_keywords):
            return idx

    # Default to first row
    return 0


def clean_merchant_name(description: str) -> str:
    """
    Extract and clean merchant name from description.

    Removes:
    - Reference numbers
    - Location codes
    - Transaction IDs
    """
    if not description or pd.isna(description):
        return ""

    description = str(description).strip()

    # Remove common patterns
    # - Remove reference numbers (e.g., #12345, REF:12345)
    description = re.sub(r"#\d+", "", description)
    description = re.sub(r"REF:\s*\w+", "", description, flags=re.IGNORECASE)

    # - Remove card numbers (last 4 digits)
    description = re.sub(r"\*+\d{4}", "", description)

    # - Remove dates
    description = re.sub(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", "", description)

    # Clean up extra spaces
    description = " ".join(description.split())

    return description


def parse_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a CSV bank statement file.

    Returns:
        List of transaction dictionaries with standardized fields
    """
    # Detect delimiter
    delimiter = detect_delimiter(file_path)

    # Detect header row
    header_row = detect_header_row(file_path, delimiter)

    # Read CSV
    df = pd.read_csv(
        file_path,
        delimiter=delimiter,
        header=header_row,
        encoding="utf-8-sig",
        skip_blank_lines=True,
    )

    # Normalize column names
    df = normalize_column_names(df)

    # Check if we have required columns
    if "date" not in df.columns or "amount" not in df.columns:
        raise ValueError("CSV must contain 'date' and 'amount' columns")

    # Parse transactions
    transactions = []

    for _, row in df.iterrows():
        # Skip rows with missing critical data
        if pd.isna(row.get("date")) or pd.isna(row.get("amount")):
            continue

        # Parse date
        transaction_date = parse_date(row["date"])
        if not transaction_date:
            continue

        # Parse amount
        amount = parse_amount(str(row["amount"]))
        if amount is None:
            continue

        # Get description
        description = (
            str(row.get("description", ""))
            if not pd.isna(row.get("description"))
            else ""
        )

        # Extract merchant name
        merchant_name = clean_merchant_name(description)
        if "merchant_name" in row and not pd.isna(row["merchant_name"]):
            merchant_name = clean_merchant_name(str(row["merchant_name"]))

        transaction = {
            "date": transaction_date,
            "amount": amount,
            "description": description,
            "merchant_name": merchant_name,
        }

        transactions.append(transaction)

    return transactions


def extract_statement_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from CSV statement (date range, account info if present).
    """
    try:
        transactions = parse_csv_file(file_path)

        if not transactions:
            return {}

        dates = [t["date"] for t in transactions if t.get("date")]

        return {
            "format_type": "csv",
            "transaction_count": len(transactions),
            "date_range": {
                "start": min(dates) if dates else None,
                "end": max(dates) if dates else None,
            },
        }
    except Exception as e:
        return {"error": str(e)}
