"""
Flash Card Job Management - Tracks flash card generation jobs.

Educational Note: Flash card jobs use AI to extract key concepts from source
content and generate question-answer pairs for studying.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_flash_card_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new flash card generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the flash cards

    Returns:
        The created job record
    """
    job = {
        "id": job_id,
        "source_id": source_id,
        "source_name": source_name,
        "direction": direction,
        "status": "pending",
        "progress": "Initializing...",
        "error": None,
        "cards": [],
        "topic_summary": None,
        "card_count": 0,
        "generation_time_seconds": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    print(f"[StudioIndex] Creating flash card job {job_id}, existing jobs: {len(index.get('flash_card_jobs', []))}")
    index["flash_card_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['flash_card_jobs'])} flash card jobs")

    return job


def update_flash_card_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a flash card job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["flash_card_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["flash_card_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_flash_card_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a flash card job by ID."""
    index = load_index(project_id)
    jobs = index.get("flash_card_jobs", [])
    print(f"[StudioIndex] Looking for job {job_id}, found {len(jobs)} flash card jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_flash_card_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List flash card jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of flash card jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("flash_card_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_flash_card_job(project_id: str, job_id: str) -> bool:
    """
    Delete a flash card job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["flash_card_jobs"])

    index["flash_card_jobs"] = [j for j in index["flash_card_jobs"] if j["id"] != job_id]

    if len(index["flash_card_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
