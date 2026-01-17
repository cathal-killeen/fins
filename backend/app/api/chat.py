"""
Chat API endpoints for file upload and processing.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
import logging
from app.api.auth import get_current_user
from app.services.file_handler import (
    save_uploaded_file,
    generate_job_id,
)
from app.services.statement_processor import StatementProcessor
from app.services.sync_job_service import SyncJobService
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


class UploadResponse(BaseModel):
    job_id: str
    message: str
    file_name: str
    file_size: int


class ProcessingStatusResponse(BaseModel):
    job_id: str
    status: str
    current_stage: str
    progress: int
    message: str
    error: Optional[str] = None
    account_match: Optional[dict] = None
    statement_metadata: Optional[dict] = None


class AccountConfirmRequest(BaseModel):
    job_id: str
    account_id: Optional[str] = None
    create_new_account: bool = False
    new_account_name: Optional[str] = None


async def process_statement_background(
    file_path: str, file_type: str, job_id: str, user_id: str
):
    """Background task to process statement."""
    processor = StatementProcessor()
    sync_job_service = SyncJobService()

    try:
        result = await processor.process_statement(
            file_path=file_path, file_type=file_type, job_id=job_id, user_id=user_id
        )

        # Update job in database
        await sync_job_service.update_job(
            job_id=job_id,
            status=result["stage"],
            stage=result["stage"],
            progress={"percentage": result["progress"], "message": result["message"]},
            error_message=result.get("error"),
            metadata=result.get("metadata", {}),
        )

    except Exception as e:
        # Update job with error status
        await sync_job_service.update_job(
            job_id=job_id,
            status="failed",
            stage="failed",
            progress={"percentage": 0, "message": f"Processing failed: {str(e)}"},
            error_message=str(e),
        )


@router.post("/upload-statement", response_model=UploadResponse)
async def upload_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """
    Upload a bank statement (CSV or PDF) for processing.

    Returns a job_id that can be used to poll for processing status.
    """
    # Generate unique job ID
    job_id = generate_job_id()

    try:
        # Save uploaded file
        file_path, file_size, file_type = await save_uploaded_file(file, job_id)

        # Create job in database
        sync_job_service = SyncJobService()
        await sync_job_service.create_job(
            user_id=str(current_user["id"]), job_id=job_id, job_type="file_upload"
        )

        # Start background processing
        background_tasks.add_task(
            process_statement_background,
            file_path,
            file_type,
            job_id,
            str(current_user["id"]),
        )

        return UploadResponse(
            job_id=job_id,
            message="File uploaded successfully. Processing started.",
            file_name=file.filename or f"statement.{file_type}",
            file_size=file_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.get("/processing-status/{job_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    job_id: str, current_user=Depends(get_current_user)
):
    """
    Get the current processing status of an uploaded statement.

    Poll this endpoint every 2 seconds while status is not 'completed' or 'failed'.
    """
    # Get job status from database
    sync_job_service = SyncJobService()
    job = await sync_job_service.get_job(job_id, user_id=str(current_user["id"]))

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    progress = job["progress"] or {}
    metadata = job["metadata"] or {}

    return ProcessingStatusResponse(
        job_id=job["id"],
        status=job["status"],
        current_stage=job["stage"] or "",
        progress=progress.get("percentage", 0),
        message=progress.get("message", ""),
        error=job["error_message"],
        account_match=metadata.get("account_match"),
        statement_metadata=metadata.get("statement_metadata"),
    )


@router.post("/confirm-account")
async def confirm_account(
    request: AccountConfirmRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """
    Confirm or create account for transaction import.

    Called after the user selects/confirms an account from the chat interface.
    """
    job_id = request.job_id

    # Check if job exists
    sync_job_service = SyncJobService()
    job = await sync_job_service.get_job(job_id, user_id=str(current_user["id"]))

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Verify job is awaiting confirmation
    if job["stage"] != "awaiting_confirmation":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not awaiting confirmation (current stage: {job['stage']})",
        )

    # Prepare account data if creating new
    new_account_data = None
    if request.create_new_account and request.new_account_name:
        metadata = job["metadata"]
        statement_metadata = metadata.get("statement_metadata", {})

        new_account_data = {
            "user_id": str(current_user["id"]),
            "account_name": request.new_account_name,
            "account_type": statement_metadata.get("account_type", "unknown"),
            "institution": statement_metadata.get("institution"),
            "account_number_last4": statement_metadata.get("account_number_last4"),
            "currency": "USD",
            "is_active": True,
        }

    # Update status to show we're resuming
    await sync_job_service.update_job(
        job_id=job_id,
        status="running",
        stage="extracting_transactions",
        progress={
            "percentage": 65,
            "message": "Account confirmed. Resuming processing...",
        },
    )

    # Resume processing in background
    async def continue_processing():
        processor = StatementProcessor()
        sync_service = SyncJobService()

        try:
            result = await processor.continue_after_confirmation(
                job_id=job_id,
                confirmed_account_id=request.account_id,
                create_new_account=request.create_new_account,
                new_account_data=new_account_data,
            )

            # Update job with result
            await sync_service.update_job(
                job_id=job_id,
                status=result["stage"],
                stage=result["stage"],
                progress={
                    "percentage": result["progress"],
                    "message": result["message"],
                },
                error_message=result.get("error"),
            )
        except Exception as e:
            # Update job with error
            await sync_service.update_job(
                job_id=job_id,
                status="failed",
                stage="failed",
                progress={"percentage": 0, "message": f"Processing failed: {str(e)}"},
                error_message=str(e),
            )

    background_tasks.add_task(continue_processing)

    return {
        "message": "Account confirmed. Continuing import...",
        "job_id": request.job_id,
    }
