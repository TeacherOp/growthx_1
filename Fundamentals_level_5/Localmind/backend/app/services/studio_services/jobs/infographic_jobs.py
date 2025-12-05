"""
Infographic Job Management - Tracks infographic generation jobs.

Educational Note: Infographic jobs use AI to extract key information from
source content and generate visual summaries using AI image generation.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_infographic_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new infographic generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the infographic

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
        "topic_title": None,
        "topic_summary": None,
        "key_sections": [],
        "image": None,
        "image_url": None,
        "image_prompt": None,
        "generation_time_seconds": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    print(f"[StudioIndex] Creating infographic job {job_id}, existing jobs: {len(index.get('infographic_jobs', []))}")
    index["infographic_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['infographic_jobs'])} infographic jobs")

    return job


def update_infographic_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update an infographic job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["infographic_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["infographic_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_infographic_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get an infographic job by ID."""
    index = load_index(project_id)
    jobs = index.get("infographic_jobs", [])
    print(f"[StudioIndex] Looking for infographic job {job_id}, found {len(jobs)} jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Infographic job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_infographic_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List infographic jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of infographic jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("infographic_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_infographic_job(project_id: str, job_id: str) -> bool:
    """
    Delete an infographic job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["infographic_jobs"])

    index["infographic_jobs"] = [j for j in index["infographic_jobs"] if j["id"] != job_id]

    if len(index["infographic_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
