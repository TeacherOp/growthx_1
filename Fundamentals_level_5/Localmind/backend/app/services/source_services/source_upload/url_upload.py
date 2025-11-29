"""
URL Upload Handler - Manages URL source uploads.

Educational Note: URLs are stored as .link files containing JSON with the URL
and metadata. The actual content fetching/processing happens in a separate step
via the web_agent_service (for websites) or youtube_service (for YouTube).

Supports:
- Website URLs (processed by web_agent)
- YouTube URLs (processed by youtube_service)
"""
import json
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from app.services.source_services import source_index_service
from app.services.background_services import task_service
from app.utils.path_utils import get_raw_dir


def upload_url(
    project_id: str,
    url: str,
    name: Optional[str] = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Add a URL source (website or YouTube link) to a project.

    Educational Note: URLs are stored as .link files containing JSON
    with the URL and metadata. The actual content fetching/processing
    happens in a separate processing step.

    Args:
        project_id: The project UUID
        url: The URL to store
        name: Optional display name (defaults to URL)
        description: Optional description

    Returns:
        Source metadata dictionary

    Raises:
        ValueError: If URL is empty or invalid format
    """
    # Basic URL validation
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    url = url.strip()

    # Check if it looks like a URL
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        raise ValueError("Invalid URL format. Must start with http:// or https://")

    # Detect if it's a YouTube URL
    is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
    link_type = 'youtube' if is_youtube else 'website'

    # Generate source ID and paths
    source_id = str(uuid.uuid4())
    stored_filename = f"{source_id}.link"
    raw_dir = get_raw_dir(project_id)

    # Create link file with URL data
    link_data = {
        "url": url,
        "type": link_type,
        "fetched": False,
        "fetched_at": None
    }

    file_path = raw_dir / stored_filename
    with open(file_path, 'w') as f:
        json.dump(link_data, f, indent=2)

    file_size = file_path.stat().st_size

    # Create source metadata
    timestamp = datetime.now().isoformat()
    source_metadata = {
        "id": source_id,
        "project_id": project_id,
        "name": name or url,
        "original_filename": url,
        "description": description,
        "category": "link",
        "mime_type": "application/json",
        "file_extension": ".link",
        "file_size": file_size,
        "stored_filename": stored_filename,
        "status": "uploaded",
        "active": False,
        "processing_info": {"link_type": link_type},
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Add to index
    source_index_service.add_source_to_index(project_id, source_metadata)

    print(f"Added URL source: {url} ({source_id})")

    # Submit background processing task
    _submit_processing_task(project_id, source_id)

    return source_metadata


def _submit_processing_task(project_id: str, source_id: str) -> None:
    """
    Submit a background task to process the URL source.

    Educational Note: URL content extraction runs in background thread
    so it doesn't block the API response.
    """
    from app.services.source_services.source_processing import source_processing_service

    task_service.submit_task(
        "source_processing",
        source_id,
        source_processing_service.process_source,
        project_id,
        source_id
    )
