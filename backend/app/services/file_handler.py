"""
File upload handling service.
"""

import os
import uuid
import magic
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import settings


def ensure_upload_dir():
    """Create upload directory if it doesn't exist."""
    upload_dir = Path(settings.TEMP_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_job_id() -> str:
    """Generate a unique job ID for file processing."""
    return str(uuid.uuid4())


def validate_file_type(file: UploadFile) -> str:
    """
    Validate file type using magic numbers.

    Returns:
        File extension ('csv' or 'pdf')

    Raises:
        HTTPException if file type is not supported
    """
    # Read first 2048 bytes to check file type
    file_header = file.file.read(2048)
    file.file.seek(0)  # Reset file pointer

    # Detect MIME type
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(file_header)

    # Check if it's a supported type
    if file_type == "text/csv" or file_type == "text/plain":
        # Additional check for CSV
        if file.filename and file.filename.endswith(".csv"):
            return "csv"
        # Check if content looks like CSV
        try:
            content = file_header.decode("utf-8")
            if "," in content or ";" in content:
                return "csv"
        except:
            pass

    if file_type == "application/pdf":
        return "pdf"

    # Fallback to filename extension
    if file.filename:
        ext = file.filename.lower().split(".")[-1]
        if ext in settings.SUPPORTED_FILE_TYPES:
            return ext

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: {file_type}. Please upload CSV or PDF files.",
    )


def validate_file_size(file: UploadFile):
    """
    Validate file size.

    Raises:
        HTTPException if file is too large
    """
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.1f}MB",
        )

    return file_size


async def save_uploaded_file(file: UploadFile, job_id: str) -> tuple[str, int, str]:
    """
    Save uploaded file to temporary directory.

    Returns:
        Tuple of (file_path, file_size, file_type)
    """
    # Validate file
    file_type = validate_file_type(file)
    file_size = validate_file_size(file)

    # Create upload directory
    upload_dir = ensure_upload_dir()

    # Generate safe filename
    safe_filename = f"{job_id}.{file_type}"
    file_path = upload_dir / safe_filename

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return str(file_path), file_size, file_type


def cleanup_temp_file(file_path: str):
    """Delete temporary file after processing."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Failed to delete temp file {file_path}: {e}")


def get_temp_file_path(job_id: str, file_type: str) -> str:
    """Get the path to a temporary file."""
    upload_dir = Path(settings.TEMP_UPLOAD_DIR)
    return str(upload_dir / f"{job_id}.{file_type}")
