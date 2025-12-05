"""
Social Post Job Management - Tracks social media post generation jobs.

Educational Note: Social post jobs use AI to generate platform-specific
content (Twitter, LinkedIn, etc.) from source materials.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_social_post_job(
    project_id: str,
    job_id: str,
    topic: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new social post generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        topic: Topic to create posts about
        direction: User's direction for the posts

    Returns:
        The created job record
    """
    job = {
        "id": job_id,
        "topic": topic,
        "direction": direction,
        "status": "pending",
        "progress": "Initializing...",
        "error": None,
        "posts": [],
        "topic_summary": None,
        "post_count": 0,
        "generation_time_seconds": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    print(f"[StudioIndex] Creating social post job {job_id}, existing jobs: {len(index.get('social_post_jobs', []))}")
    index["social_post_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['social_post_jobs'])} social post jobs")

    return job


def update_social_post_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a social post job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["social_post_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["social_post_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_social_post_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a social post job by ID."""
    index = load_index(project_id)
    jobs = index.get("social_post_jobs", [])
    print(f"[StudioIndex] Looking for social post job {job_id}, found {len(jobs)} jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Social post job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_social_post_jobs(project_id: str) -> List[Dict[str, Any]]:
    """
    List social post jobs.

    Args:
        project_id: The project UUID

    Returns:
        List of social post jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("social_post_jobs", [])

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_social_post_job(project_id: str, job_id: str) -> bool:
    """
    Delete a social post job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["social_post_jobs"])

    index["social_post_jobs"] = [j for j in index["social_post_jobs"] if j["id"] != job_id]

    if len(index["social_post_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
