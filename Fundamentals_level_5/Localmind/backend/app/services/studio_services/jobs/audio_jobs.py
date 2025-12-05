"""
Audio Job Management - Tracks audio generation jobs.

Educational Note: Audio jobs generate podcast-style content from source materials.
Uses ElevenLabs for text-to-speech synthesis.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_audio_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new audio generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the audio

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
        "audio_path": None,
        "audio_filename": None,
        "audio_url": None,
        "script_path": None,
        "audio_info": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    index["audio_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_audio_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update an audio job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["audio_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["audio_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_audio_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get an audio job by ID."""
    index = load_index(project_id)

    for job in index["audio_jobs"]:
        if job["id"] == job_id:
            return job

    return None


def list_audio_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List audio jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of audio jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("audio_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_audio_job(project_id: str, job_id: str) -> bool:
    """
    Delete an audio job from the index.

    Note: This doesn't delete the actual audio file.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["audio_jobs"])

    index["audio_jobs"] = [j for j in index["audio_jobs"] if j["id"] != job_id]

    if len(index["audio_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
