"""
File Upload Handler - Manages file uploads for sources.

Educational Note: This module handles uploading files (PDF, DOCX, images, audio, etc.)
and creating source entries in the index. Processing is triggered as a background task.

Supports:
- Direct file uploads from the frontend
- Creating sources from already-saved files (e.g., Google Drive imports)
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from werkzeug.datastructures import FileStorage

from app.services.source_services import source_index_service
from app.services.background_services import task_service
from app.utils.path_utils import get_raw_dir
from app.utils.file_utils import (
    ALLOWED_EXTENSIONS,
    is_allowed_file,
    get_file_info,
    validate_file_size,
)


def upload_file(
    project_id: str,
    file: FileStorage,
    name: Optional[str] = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Upload a new source file to a project.

    Educational Note: This function:
    1. Validates the file type and size
    2. Saves the file to the raw/ directory
    3. Creates metadata in the sources index
    4. Triggers background processing

    Args:
        project_id: The project UUID
        file: The uploaded file (Flask FileStorage)
        name: Optional display name (defaults to original filename)
        description: Optional description of the source

    Returns:
        Source metadata dictionary

    Raises:
        ValueError: If file type is not allowed or file is empty
    """
    # Validate file
    if not file or not file.filename:
        raise ValueError("No file provided")

    original_filename = file.filename
    if not is_allowed_file(original_filename):
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS.keys()))
        raise ValueError(f"File type not allowed. Allowed types: {allowed}")

    # Get file info
    ext, category, mime_type = get_file_info(original_filename)

    # Generate source ID and paths
    source_id = str(uuid.uuid4())
    stored_filename = f"{source_id}{ext}"
    raw_dir = get_raw_dir(project_id)

    # Save the file
    file_path = raw_dir / stored_filename
    file.save(str(file_path))

    # Get file size
    file_size = file_path.stat().st_size

    # Validate file size (e.g., images have 5MB limit)
    size_error = validate_file_size(original_filename, file_size)
    if size_error:
        # Delete the saved file and raise error
        file_path.unlink()
        raise ValueError(size_error)

    # Create source metadata
    timestamp = datetime.now().isoformat()
    source_metadata = {
        "id": source_id,
        "project_id": project_id,
        "name": name or original_filename,
        "original_filename": original_filename,
        "description": description,
        "category": category,
        "mime_type": mime_type,
        "file_extension": ext,
        "file_size": file_size,
        "stored_filename": stored_filename,
        "status": "uploaded",
        "active": False,
        "processing_info": None,
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Add to index
    source_index_service.add_source_to_index(project_id, source_metadata)

    print(f"Uploaded source: {source_metadata['name']} ({source_id})")

    # Submit processing as a background task
    _submit_processing_task(project_id, source_id)

    return source_metadata


def create_from_existing_file(
    project_id: str,
    file_path: Path,
    name: str,
    original_filename: str,
    category: str,
    mime_type: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Create a source entry from an already-saved file.

    Educational Note: This is used when a file is downloaded/saved externally
    (e.g., from Google Drive) and we need to create the source index entry.
    The file should already exist at the given path.

    Args:
        project_id: The project UUID
        file_path: Path where the file is already saved
        name: Display name for the source
        original_filename: Original filename (used for extension)
        category: Source category (document, image, audio, etc.)
        mime_type: MIME type of the file
        description: Optional description

    Returns:
        Source metadata dictionary

    Raises:
        ValueError: If file does not exist
    """
    if not file_path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    # Get extension from stored filename
    ext = file_path.suffix.lower()
    source_id = file_path.stem  # UUID is the filename without extension

    # Get file size
    file_size = file_path.stat().st_size

    # Create source metadata
    timestamp = datetime.now().isoformat()
    source_metadata = {
        "id": source_id,
        "project_id": project_id,
        "name": name,
        "original_filename": original_filename,
        "description": description,
        "category": category,
        "mime_type": mime_type,
        "file_extension": ext,
        "file_size": file_size,
        "stored_filename": file_path.name,
        "status": "uploaded",
        "active": False,
        "processing_info": None,
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Add to index
    source_index_service.add_source_to_index(project_id, source_metadata)

    print(f"Created source from file: {name} ({source_id})")

    # Submit processing as a background task
    _submit_processing_task(project_id, source_id)

    return source_metadata


def _submit_processing_task(project_id: str, source_id: str) -> None:
    """
    Submit a background task to process the source.

    Educational Note: We import source_processing_service here to avoid
    circular imports at module load time.
    """
    from app.services.source_services.source_processing import source_processing_service

    task_service.submit_task(
        "source_processing",
        source_id,
        source_processing_service.process_source,
        project_id,
        source_id
    )
