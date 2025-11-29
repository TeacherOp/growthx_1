"""
Source Index Service - CRUD operations for the sources index.

Educational Note: This service manages the sources_index.json file which stores
metadata for all sources in a project. Separating index operations from the
main source_service keeps concerns focused and files smaller.

The index structure:
{
    "sources": [
        {
            "id": "uuid",
            "name": "...",
            "status": "uploaded|processing|embedding|ready|error",
            ... other metadata
        }
    ],
    "last_updated": "ISO timestamp"
}
"""
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.utils.path_utils import get_sources_index_path


def load_index(project_id: str) -> Dict[str, Any]:
    """
    Load the sources index for a project.

    Educational Note: Returns empty structure if index doesn't exist.
    This is safe to call for new projects.

    Args:
        project_id: The project UUID

    Returns:
        Dict with "sources" list and "last_updated" timestamp
    """
    index_path = get_sources_index_path(project_id)

    if not index_path.exists():
        return {
            "sources": [],
            "last_updated": datetime.now().isoformat()
        }

    try:
        with open(index_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "sources": [],
            "last_updated": datetime.now().isoformat()
        }


def save_index(project_id: str, index_data: Dict[str, Any]) -> None:
    """
    Save the sources index for a project.

    Educational Note: Updates last_updated timestamp automatically.
    The get_sources_index_path function ensures the parent directory exists.

    Args:
        project_id: The project UUID
        index_data: The index data to save
    """
    index_path = get_sources_index_path(project_id)

    index_data["last_updated"] = datetime.now().isoformat()
    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=2)


def add_source_to_index(project_id: str, source_metadata: Dict[str, Any]) -> None:
    """
    Add a new source to the index.

    Args:
        project_id: The project UUID
        source_metadata: Complete source metadata dict
    """
    index = load_index(project_id)
    index["sources"].append(source_metadata)
    save_index(project_id, index)


def remove_source_from_index(project_id: str, source_id: str) -> bool:
    """
    Remove a source from the index.

    Args:
        project_id: The project UUID
        source_id: The source UUID to remove

    Returns:
        True if source was found and removed, False otherwise
    """
    index = load_index(project_id)
    original_count = len(index["sources"])

    index["sources"] = [s for s in index["sources"] if s["id"] != source_id]

    if len(index["sources"]) < original_count:
        save_index(project_id, index)
        return True

    return False


def get_source_from_index(project_id: str, source_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a source's metadata from the index.

    Args:
        project_id: The project UUID
        source_id: The source UUID

    Returns:
        Source metadata dict or None if not found
    """
    index = load_index(project_id)

    for source in index["sources"]:
        if source["id"] == source_id:
            return source

    return None


def update_source_in_index(
    project_id: str,
    source_id: str,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update a source's metadata in the index.

    Educational Note: This is a generic update function. Pass a dict
    with the fields you want to update.

    Args:
        project_id: The project UUID
        source_id: The source UUID
        updates: Dict of fields to update

    Returns:
        Updated source metadata or None if not found
    """
    index = load_index(project_id)

    for i, source in enumerate(index["sources"]):
        if source["id"] == source_id:
            # Apply updates
            for key, value in updates.items():
                if value is not None:
                    source[key] = value

            source["updated_at"] = datetime.now().isoformat()
            index["sources"][i] = source
            save_index(project_id, index)

            return source

    return None


def list_sources_from_index(project_id: str) -> List[Dict[str, Any]]:
    """
    List all sources from the index, sorted by created_at (newest first).

    Args:
        project_id: The project UUID

    Returns:
        List of source metadata dicts
    """
    index = load_index(project_id)

    return sorted(
        index["sources"],
        key=lambda s: s.get("created_at", ""),
        reverse=True
    )
