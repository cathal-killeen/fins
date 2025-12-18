"""
PDF parsing utilities for bank statements.
"""
import pdfplumber
import PyPDF2
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text from a PDF file.

    Uses pdfplumber as primary method, falls back to PyPDF2 if needed.
    """
    text = ""

    try:
        # Try pdfplumber first (better for tables)
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber failed, trying PyPDF2: {e}")

        # Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e2:
            print(f"PyPDF2 also failed: {e2}")
            raise ValueError(f"Could not extract text from PDF: {e2}")

    return text


def extract_tables_from_pdf(file_path: str) -> List[List[List[str]]]:
    """
    Extract tables from PDF using pdfplumber.

    Returns:
        List of tables (one per page), where each table is a list of rows
    """
    all_tables = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
    except Exception as e:
        print(f"Could not extract tables: {e}")

    return all_tables


def find_transaction_section(text: str) -> str:
    """
    Find and extract the transaction section from PDF text.

    Looks for common section headers like:
    - Transactions
    - Activity
    - Transaction History
    - Account Activity
    """
    # Common section headers
    section_patterns = [
        r'(?i)transactions?(?:\s+history)?',
        r'(?i)account\s+activity',
        r'(?i)transaction\s+details?',
        r'(?i)activity\s+summary',
    ]

    for pattern in section_patterns:
        match = re.search(pattern, text)
        if match:
            # Return text from this point onwards
            return text[match.start():]

    # If no section found, return all text
    return text


def parse_transaction_from_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Try to parse a transaction from a text line.

    Common patterns:
    - 01/15/2025  AMAZON.COM  -$50.00
    - 2025-01-15  Starbucks  $5.50
    - Jan 15  Grocery Store  50.00 DR
    """
    line = line.strip()
    if not line:
        return None

    # Pattern: date (various formats) + description + amount
    # This is a simplified pattern - real implementation would be more robust
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|[A-Z][a-z]{2}\s+\d{1,2})'
    amount_pattern = r'[\$€£]?\s*([+-]?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:DR|CR)?'

    # Try to find date and amount
    date_match = re.search(date_pattern, line)
    amount_matches = re.findall(amount_pattern, line)

    if date_match and amount_matches:
        # Extract components
        date_str = date_match.group(1)

        # Get description (text between date and amount)
        desc_start = date_match.end()
        amount_pos = line.rfind(amount_matches[-1])
        description = line[desc_start:amount_pos].strip()

        return {
            'raw_line': line,
            'date_str': date_str,
            'description': description,
            'amount_str': amount_matches[-1],
        }

    return None


def parse_pdf_with_ai_help(file_path: str) -> Dict[str, Any]:
    """
    Extract basic structure from PDF for AI analysis.

    Returns raw text and tables that AI can analyze.
    """
    # Extract text
    text = extract_text_from_pdf(file_path)

    # Extract tables
    tables = extract_tables_from_pdf(file_path)

    # Find transaction section
    transaction_text = find_transaction_section(text)

    return {
        'full_text': text[:5000],  # First 5000 chars
        'transaction_section': transaction_text[:3000],  # First 3000 chars of transactions
        'tables': tables[:3] if tables else [],  # First 3 tables
        'has_tables': len(tables) > 0,
    }


def extract_account_info_from_pdf(text: str) -> Dict[str, Any]:
    """
    Try to extract account information from PDF text.

    Looks for:
    - Account number
    - Account type
    - Bank name
    """
    info = {}

    # Look for account number (various patterns)
    account_patterns = [
        r'Account\s+(?:Number|#):\s*(\d+)',
        r'Account:\s*(\d+)',
        r'(?:Acct|A/C)\s*[:#]\s*(\d+)',
    ]

    for pattern in account_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            account_num = match.group(1)
            # Only keep last 4 digits
            info['account_number_last4'] = account_num[-4:] if len(account_num) >= 4 else account_num
            break

    # Look for account type
    if re.search(r'\bchecking\b', text, re.IGNORECASE):
        info['account_type'] = 'checking'
    elif re.search(r'\bsavings\b', text, re.IGNORECASE):
        info['account_type'] = 'savings'
    elif re.search(r'\bcredit\s+card\b', text, re.IGNORECASE):
        info['account_type'] = 'credit_card'

    # Try to identify bank (common bank names)
    banks = ['Chase', 'Bank of America', 'Wells Fargo', 'Citibank', 'Capital One', 'US Bank']
    for bank in banks:
        if bank.lower() in text.lower():
            info['institution'] = bank
            break

    return info


def parse_pdf_file(file_path: str) -> Dict[str, Any]:
    """
    Main PDF parsing function.

    Returns structure suitable for AI analysis.
    """
    try:
        # Extract content
        pdf_data = parse_pdf_with_ai_help(file_path)

        # Try to extract account info
        account_info = extract_account_info_from_pdf(pdf_data['full_text'])

        return {
            'format_type': 'pdf',
            'content': pdf_data,
            'account_info': account_info,
            'requires_ai_parsing': True,  # PDF always needs AI help
        }
    except Exception as e:
        return {
            'error': f"Failed to parse PDF: {str(e)}",
            'format_type': 'pdf',
        }
