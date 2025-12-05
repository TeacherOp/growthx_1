"""
UI Component Job Management - Tracks component generation jobs.

Educational Note: Component jobs use AI to generate reusable UI components
(buttons, cards, forms, etc.) with multiple variations using HTML/CSS/Tailwind.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_component_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new component generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the components

    Returns:
        The created job record
    """
    job = {
        "id": job_id,
        "source_id": source_id,
        "source_name": source_name,
        "direction": direction,
        "status": "pending",
        "status_message": "Initializing...",
        "error_message": None,
        # Component plan fields
        "component_category": None,
        "component_description": None,
        "variations_planned": [],
        "technical_notes": None,
        # Generated content
        "components": [],  # List of {variation_name, filename, description, preview_url, char_count}
        "usage_notes": None,
        # Metadata
        "iterations": None,
        "input_tokens": None,
        "output_tokens": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    index["component_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_component_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a component job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["component_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["component_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_component_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a component job by ID."""
    index = load_index(project_id)
    jobs = index.get("component_jobs", [])

    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def list_component_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List component jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of component jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("component_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_component_job(project_id: str, job_id: str) -> bool:
    """
    Delete a component job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["component_jobs"])

    index["component_jobs"] = [j for j in index["component_jobs"] if j["id"] != job_id]

    if len(index["component_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
