"""
Video Job Management - Tracks video generation jobs.

Educational Note: Video jobs use AI video generation APIs (like Google Veo)
to create short video clips from prompts derived from source content.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_video_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
    number_of_videos: int = 1
) -> Dict[str, Any]:
    """
    Create a new video generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction/guidance for video generation
        aspect_ratio: "16:9" or "16:10"
        duration_seconds: 5-8 seconds
        number_of_videos: 1-4 videos

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
        # Generation parameters
        "aspect_ratio": aspect_ratio,
        "duration_seconds": duration_seconds,
        "number_of_videos": number_of_videos,
        # Generated content
        "videos": [],  # List of {filename, path, uri, preview_url, download_url}
        "generated_prompt": None,  # Will be set by video_prompt_service
        # Metadata
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    index["video_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_video_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a video job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["video_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["video_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_video_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a video job by ID."""
    index = load_index(project_id)
    jobs = index.get("video_jobs", [])

    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def list_video_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List video jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of video jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("video_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_video_job(project_id: str, job_id: str) -> bool:
    """
    Delete a video job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["video_jobs"])

    index["video_jobs"] = [j for j in index["video_jobs"] if j["id"] != job_id]

    if len(index["video_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
