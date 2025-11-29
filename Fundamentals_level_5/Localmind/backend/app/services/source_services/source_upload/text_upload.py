"""
Text Upload Handler - Manages pasted text source uploads.

Educational Note: Pasted text is stored as a .txt file in the raw/ directory.
This is the simplest source type - the raw content IS the processed content
(after adding page markers for large texts).
"""
import uuid
from datetime import datetime
from typing import Dict, Any

from app.services.source_services import source_index_service
from app.services.background_services import task_service
from app.utils.path_utils import get_raw_dir


def upload_text(
    project_id: str,
    content: str,
    name: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Add a pasted text source to a project.

    Educational Note: Pasted text is stored as a .txt file.
    Processing will add page markers for large texts.

    Args:
        project_id: The project UUID
        content: The pasted text content
        name: Display name for the source (required)
        description: Optional description

    Returns:
        Source metadata dictionary

    Raises:
        ValueError: If content or name is empty
    """
    # Validate inputs
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")

    if not name or not name.strip():
        raise ValueError("Name is required for pasted text")

    content = content.strip()
    name = name.strip()

    # Generate source ID and paths
    source_id = str(uuid.uuid4())
    stored_filename = f"{source_id}.txt"
    raw_dir = get_raw_dir(project_id)

    # Save the text content
    file_path = raw_dir / stored_filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    file_size = file_path.stat().st_size

    # Create source metadata
    timestamp = datetime.now().isoformat()
    source_metadata = {
        "id": source_id,
        "project_id": project_id,
        "name": name,
        "original_filename": f"{name}.txt",
        "description": description,
        "category": "document",
        "mime_type": "text/plain",
        "file_extension": ".txt",
        "file_size": file_size,
        "stored_filename": stored_filename,
        "status": "uploaded",
        "active": False,
        "processing_info": {"source_type": "pasted_text"},
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Add to index
    source_index_service.add_source_to_index(project_id, source_metadata)

    print(f"Added text source: {name} ({source_id})")

    # Submit processing as background task
    _submit_processing_task(project_id, source_id)

    return source_metadata


def _submit_processing_task(project_id: str, source_id: str) -> None:
    """
    Submit a background task to process the text source.

    Educational Note: Even text files go through processing to add
    page markers for consistent chunking behavior.
    """
    from app.services.source_services.source_processing import source_processing_service

    task_service.submit_task(
        "source_processing",
        source_id,
        source_processing_service.process_source,
        project_id,
        source_id
    )
