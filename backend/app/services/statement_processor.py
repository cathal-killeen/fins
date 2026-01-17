"""
Statement processing service - orchestrates the 7-stage pipeline.

Processing stages:
1. File parsing (CSV or PDF)
2. AI structure analysis
3. Account matching
4. User confirmation (pause)
5. Transaction extraction
6. Duplicate detection
7. Database save
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
from sqlalchemy.orm import Session

from app.utils.csv_parser import parse_csv_file, extract_statement_metadata
from app.utils.pdf_parser import parse_pdf_file
from app.services.ai_service import (
    analyze_statement_structure,
    extract_transactions,
    suggest_account_match,
)
from app.services.file_handler import cleanup_uploaded_file
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService
from app.services.sync_job_service import SyncJobService
from app.models.account import Account


class ProcessingStage:
    """Constants for processing stages."""

    UPLOADING = "uploading"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    MATCHING_ACCOUNT = "matching_account"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    EXTRACTING_TRANSACTIONS = "extracting_transactions"
    CHECKING_DUPLICATES = "checking_duplicates"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStatus:
    """Status tracking for processing job."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.stage = ProcessingStage.UPLOADING
        self.progress = 0
        self.message = "File uploaded, initializing processing..."
        self.error = None
        self.metadata = {}

    def update(self, stage: str, progress: int, message: str):
        """Update processing status."""
        self.stage = stage
        self.progress = progress
        self.message = message

    def set_error(self, error: str):
        """Set error status."""
        self.stage = ProcessingStage.FAILED
        self.error = error
        self.message = f"Processing failed: {error}"


class StatementProcessor:
    """Main orchestrator for statement processing pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.account_service = AccountService(db)
        self.transaction_service = TransactionService(db)
        self.sync_job_service = SyncJobService(db)

    async def process_statement(
        self, file_path: str, file_type: str, job_id: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Process a bank statement through the complete pipeline.

        Args:
            file_path: Path to uploaded file
            file_type: 'csv' or 'pdf'
            job_id: Unique job identifier
            user_id: User ID

        Returns:
            Processing result dictionary
        """
        status = ProcessingStatus(job_id)

        try:
            # Stage 1: Parse file (10% -> 25%)
            status.update(
                ProcessingStage.PARSING, 10, f"Parsing {file_type.upper()} file..."
            )
            parsed_content = await self._parse_file(file_path, file_type)

            if "error" in parsed_content:
                status.set_error(parsed_content["error"])
                return self._build_result(status, parsed_content)

            status.update(ProcessingStage.PARSING, 25, f"File parsed successfully")

            # Stage 2: AI structure analysis (25% -> 40%)
            status.update(
                ProcessingStage.ANALYZING,
                30,
                "Analyzing statement structure with AI...",
            )

            statement_metadata = await analyze_statement_structure(parsed_content)

            status.update(
                ProcessingStage.ANALYZING,
                40,
                f"Identified {statement_metadata.get('institution', 'unknown')} statement",
            )

            # Stage 3: Account matching (40% -> 55%)
            status.update(
                ProcessingStage.MATCHING_ACCOUNT, 45, "Matching to your accounts..."
            )

            user_accounts = await self._get_user_accounts(user_id)
            account_match = await suggest_account_match(
                statement_metadata, user_accounts
            )

            status.update(ProcessingStage.MATCHING_ACCOUNT, 55, "Account match found")

            # Stage 4: Pause for user confirmation
            status.update(
                ProcessingStage.AWAITING_CONFIRMATION,
                60,
                "Waiting for account confirmation...",
            )

            # Store intermediate results
            status.metadata = {
                "statement_metadata": statement_metadata,
                "account_match": account_match,
                "parsed_content": parsed_content,
                "file_path": file_path,
            }

            # Return here - processing continues after user confirms account
            return self._build_result(
                status,
                {
                    "requires_confirmation": True,
                    "statement_metadata": statement_metadata,
                    "account_match": account_match,
                },
            )

        except Exception as e:
            status.set_error(str(e))
            await self._cleanup(file_path)
            return self._build_result(status, {"error": str(e)})

    async def continue_after_confirmation(
        self,
        job_id: str,
        confirmed_account_id: str,
        create_new_account: bool = False,
        new_account_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Continue processing after user confirms account.

        Args:
            job_id: Job identifier
            confirmed_account_id: Account ID (existing or newly created)
            create_new_account: Whether to create new account
            new_account_data: Data for new account creation

        Returns:
            Processing result dictionary
        """
        # Retrieve stored status and metadata
        status = await self._get_job_status(job_id)
        metadata = status.metadata

        try:
            # Create new account if requested
            if create_new_account and new_account_data:
                account = await self._create_account(new_account_data)
                confirmed_account_id = account["id"]

            # Stage 5: Extract transactions (60% -> 75%)
            status.update(
                ProcessingStage.EXTRACTING_TRANSACTIONS,
                65,
                "Extracting transactions...",
            )

            parsed_content = metadata["parsed_content"]
            statement_metadata = metadata["statement_metadata"]

            # For CSV, parsed_content might already be transactions
            # For PDF, we need to extract from the content
            if parsed_content.get("format_type") == "csv":
                # CSV parser already returned transactions
                transactions = parsed_content.get("transactions", [])
            else:
                # PDF - need AI extraction
                transactions = await extract_transactions(
                    parsed_content, statement_metadata
                )

            status.update(
                ProcessingStage.EXTRACTING_TRANSACTIONS,
                75,
                f"Extracted {len(transactions)} transactions",
            )

            # Stage 6: Check for duplicates (75% -> 85%)
            status.update(
                ProcessingStage.CHECKING_DUPLICATES,
                80,
                "Checking for duplicate transactions...",
            )

            duplicate_check = await self._check_duplicates(
                confirmed_account_id, transactions
            )

            new_transactions = duplicate_check["new"]
            duplicate_count = len(duplicate_check["duplicates"])

            status.update(
                ProcessingStage.CHECKING_DUPLICATES,
                85,
                f"Found {duplicate_count} duplicates, {len(new_transactions)} new transactions",
            )

            # Stage 7: Save to database (85% -> 100%)
            status.update(
                ProcessingStage.SAVING, 90, "Saving transactions to database..."
            )

            saved_count = await self._save_transactions(
                confirmed_account_id, new_transactions
            )

            status.update(
                ProcessingStage.COMPLETED,
                100,
                f"Successfully imported {saved_count} transactions",
            )

            # Cleanup uploaded file
            await self._cleanup(metadata.get("file_path"))

            return self._build_result(
                status,
                {
                    "completed": True,
                    "account_id": confirmed_account_id,
                    "transactions_extracted": len(transactions),
                    "transactions_imported": saved_count,
                    "duplicates_skipped": duplicate_count,
                },
            )

        except Exception as e:
            status.set_error(str(e))
            await self._cleanup(metadata.get("file_path"))
            return self._build_result(status, {"error": str(e)})

    async def _parse_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Parse CSV or PDF file."""
        try:
            if file_type == "csv":
                # Parse CSV
                transactions = parse_csv_file(file_path)
                metadata = extract_statement_metadata(file_path)

                return {"format_type": "csv", "transactions": transactions, **metadata}
            else:
                # Parse PDF
                result = parse_pdf_file(file_path)
                return result

        except Exception as e:
            return {"error": f"Failed to parse {file_type}: {str(e)}"}

    async def _get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's existing accounts."""
        return self.account_service.get_user_accounts(user_id)

    async def _create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new account."""
        user_id = account_data.pop("user_id", None)
        return self.account_service.create_account(user_id, account_data)

    async def _check_duplicates(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check for duplicate transactions.

        Returns:
            {'duplicates': [...], 'new': [...]}
        """
        return self.transaction_service.check_duplicates(account_id, transactions)

    async def _save_transactions(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> int:
        """
        Save transactions to database.

        Returns:
            Number of transactions saved
        """
        # Get user_id from account
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        user_id = str(account.user_id)
        return self.transaction_service.save_transactions(
            account_id, user_id, transactions
        )

    async def _get_job_status(self, job_id: str) -> ProcessingStatus:
        """Retrieve job status from database."""
        job = self.sync_job_service.get_job(job_id)

        if not job:
            # Create mock status if job doesn't exist
            status = ProcessingStatus(job_id)
            status.metadata = {}
            return status

        # Convert job to ProcessingStatus
        status = ProcessingStatus(job_id)
        status.stage = job["stage"]
        status.progress = job["progress"].get("percentage", 0)
        status.message = job["progress"].get("message", "")
        status.error = job["error_message"]
        status.metadata = job["metadata"]
        return status

    async def _cleanup(self, file_path: Optional[str]):
        """Clean up temporary files."""
        if file_path:
            try:
                cleanup_uploaded_file(file_path)
            except Exception as e:
                # Log error but don't fail processing
                print(f"Failed to cleanup file {file_path}: {e}")

    def _build_result(
        self, status: ProcessingStatus, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build result dictionary."""
        return {
            "job_id": status.job_id,
            "stage": status.stage,
            "progress": status.progress,
            "message": status.message,
            "error": status.error,
            "metadata": status.metadata,
            **data,
        }
