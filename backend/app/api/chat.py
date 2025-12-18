"""
Chat API endpoints for file upload and processing.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.auth import get_current_user
from app.services.file_handler import (
    save_uploaded_file,
    generate_job_id,
    cleanup_temp_file
)
from app.services.statement_processor import StatementProcessor
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

router = APIRouter()

# In-memory storage for job status (temporary - will be replaced with database)
job_statuses: Dict[str, Dict[str, Any]] = {}


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


class AccountConfirmRequest(BaseModel):
    job_id: str
    account_id: Optional[str] = None
    create_new_account: bool = False
    new_account_name: Optional[str] = None


async def process_statement_background(
    file_path: str,
    file_type: str,
    job_id: str,
    user_id: str,
    db: Session
):
    """Background task to process statement."""
    processor = StatementProcessor(db)

    try:
        result = await processor.process_statement(
            file_path=file_path,
            file_type=file_type,
            job_id=job_id,
            user_id=user_id
        )

        # Store result in job_statuses
        job_statuses[job_id] = result

    except Exception as e:
        # Store error in job_statuses
        job_statuses[job_id] = {
            'job_id': job_id,
            'stage': 'failed',
            'progress': 0,
            'message': f"Processing failed: {str(e)}",
            'error': str(e)
        }


@router.post("/upload-statement", response_model=UploadResponse)
async def upload_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
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

        # Initialize job status
        job_statuses[job_id] = {
            'job_id': job_id,
            'stage': 'uploading',
            'progress': 5,
            'message': 'File uploaded, starting processing...',
            'error': None
        }

        # Start background processing
        background_tasks.add_task(
            process_statement_background,
            file_path,
            file_type,
            job_id,
            current_user.id,
            db
        )

        return UploadResponse(
            job_id=job_id,
            message=f"File uploaded successfully. Processing started.",
            file_name=file.filename or f"statement.{file_type}",
            file_size=file_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("/processing-status/{job_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    job_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current processing status of an uploaded statement.

    Poll this endpoint every 2 seconds while status is not 'completed' or 'failed'.
    """
    # Get job status from in-memory storage
    # TODO: Replace with database query
    if job_id not in job_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    status = job_statuses[job_id]

    return ProcessingStatusResponse(
        job_id=status['job_id'],
        status=status['stage'],
        current_stage=status['message'],
        progress=status['progress'],
        message=status['message'],
        error=status.get('error')
    )


@router.post("/confirm-account")
async def confirm_account(
    request: AccountConfirmRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm or create account for transaction import.

    Called after the user selects/confirms an account from the chat interface.
    """
    job_id = request.job_id

    # Check if job exists
    if job_id not in job_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    # Get current job status
    status = job_statuses[job_id]

    # Verify job is awaiting confirmation
    if status['stage'] != 'awaiting_confirmation':
        raise HTTPException(
            status_code=400,
            detail=f"Job is not awaiting confirmation (current stage: {status['stage']})"
        )

    # Prepare account data if creating new
    new_account_data = None
    if request.create_new_account and request.new_account_name:
        new_account_data = {
            'user_id': current_user.id,
            'account_name': request.new_account_name,
            'account_type': status['metadata'].get('statement_metadata', {}).get('account_type', 'unknown'),
            'institution': status['metadata'].get('statement_metadata', {}).get('institution'),
            'account_number_last4': status['metadata'].get('statement_metadata', {}).get('account_number_last4'),
            'currency': 'USD',
            'is_active': True
        }

    # Update status to show we're resuming
    job_statuses[job_id].update({
        'stage': 'extracting_transactions',
        'progress': 65,
        'message': 'Account confirmed. Resuming processing...'
    })

    # Resume processing in background
    async def continue_processing():
        processor = StatementProcessor(db)
        try:
            result = await processor.continue_after_confirmation(
                job_id=job_id,
                confirmed_account_id=request.account_id,
                create_new_account=request.create_new_account,
                new_account_data=new_account_data
            )
            job_statuses[job_id] = result
        except Exception as e:
            job_statuses[job_id].update({
                'stage': 'failed',
                'message': f"Processing failed: {str(e)}",
                'error': str(e)
            })

    background_tasks.add_task(continue_processing)

    return {
        "message": "Account confirmed. Continuing import...",
        "job_id": request.job_id
    }
