"""
Research Upload Handler - Manages deep research source creation.

Educational Note: Deep research sources are created by an AI agent that:
1. Searches the web for information on a topic
2. Analyzes any provided reference links
3. Synthesizes findings into a comprehensive document

The research request is stored as a .research JSON file containing:
- topic: The main research topic
- description: Focus areas and specific questions to answer
- links: Optional list of reference URLs to include
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

from app.services.source_services import source_index_service
from app.services.background_services import task_service
from app.utils.path_utils import get_raw_dir


def upload_research(
    project_id: str,
    topic: str,
    description: str,
    links: List[str] = None
) -> Dict[str, Any]:
    """
    Create a deep research source for a project.

    Educational Note: This creates a .research file containing the research
    parameters. The actual research is performed by a background task using
    an AI agent with web search capabilities.

    Args:
        project_id: The project UUID
        topic: The main research topic (required)
        description: Focus areas and questions to answer (required, min 50 chars)
        links: Optional list of reference URLs to analyze

    Returns:
        Source metadata dictionary

    Raises:
        ValueError: If topic or description is invalid
    """
    # Validate inputs
    if not topic or not topic.strip():
        raise ValueError("Topic is required")

    if not description or len(description.strip()) < 50:
        raise ValueError("Description must be at least 50 characters")

    topic = topic.strip()
    description = description.strip()
    links = links or []

    # Validate links are proper URLs
    validated_links = []
    for link in links:
        link = link.strip()
        if link:
            # Basic URL validation - must start with http(s)://
            if not link.startswith(('http://', 'https://')):
                link = f"https://{link}"
            validated_links.append(link)

    # Generate source ID and paths
    source_id = str(uuid.uuid4())
    stored_filename = f"{source_id}.research"
    raw_dir = get_raw_dir(project_id)

    # Create research request JSON
    research_request = {
        "topic": topic,
        "description": description,
        "links": validated_links,
        "created_at": datetime.now().isoformat()
    }

    # Save the research request
    file_path = raw_dir / stored_filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(research_request, f, indent=2)

    file_size = file_path.stat().st_size

    # Create a display name from the topic (truncate if too long)
    display_name = topic if len(topic) <= 50 else topic[:47] + "..."

    # Create source metadata
    timestamp = datetime.now().isoformat()
    source_metadata = {
        "id": source_id,
        "project_id": project_id,
        "name": display_name,
        "original_filename": f"{display_name}.research",
        "description": description[:200] if len(description) > 200 else description,
        "category": "document",  # Research outputs are documents
        "mime_type": "application/json",
        "file_extension": ".research",
        "file_size": file_size,
        "stored_filename": stored_filename,
        "status": "uploaded",
        "active": False,
        "processing_info": {
            "source_type": "deep_research",
            "topic": topic,
            "link_count": len(validated_links)
        },
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Add to index
    source_index_service.add_source_to_index(project_id, source_metadata)

    print(f"Created research source: {display_name} ({source_id})")

    # Submit processing as background task
    _submit_processing_task(project_id, source_id)

    return source_metadata


def _submit_processing_task(project_id: str, source_id: str) -> None:
    """
    Submit a background task to process the research source.

    Educational Note: Research processing can take several minutes as the
    AI agent searches the web and synthesizes findings. This runs in background.
    """
    from app.services.source_services.source_processing import source_processing_service

    task_service.submit_task(
        "source_processing",
        source_id,
        source_processing_service.process_source,
        project_id,
        source_id
    )
