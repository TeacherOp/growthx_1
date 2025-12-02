"""
Studio Index Service - Tracks studio generation jobs (audio, etc.).

Educational Note: This service manages a studio_index.json file that tracks
all studio content generation jobs. Similar to sources_index.json but for
generated content.

Job Status Flow:
    pending → processing → ready
                        → error

The frontend polls the status endpoint to know when content is ready.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.utils.path_utils import get_studio_dir


def _get_index_path(project_id: str) -> Path:
    """Get the studio index file path for a project."""
    return get_studio_dir(project_id) / "studio_index.json"


def load_index(project_id: str) -> Dict[str, Any]:
    """
    Load the studio index for a project.

    Returns empty structure if index doesn't exist.
    """
    index_path = _get_index_path(project_id)

    default_index = {
        "audio_jobs": [],
        "ad_jobs": [],
        "flash_card_jobs": [],
        "mind_map_jobs": [],
        "quiz_jobs": [],
        "social_post_jobs": [],
        "last_updated": datetime.now().isoformat()
    }

    if not index_path.exists():
        return default_index

    try:
        with open(index_path, 'r') as f:
            data = json.load(f)
            # Ensure job arrays exist (migration for existing indexes)
            needs_save = False
            if "ad_jobs" not in data:
                data["ad_jobs"] = []
                needs_save = True
            if "flash_card_jobs" not in data:
                data["flash_card_jobs"] = []
                needs_save = True
            if "mind_map_jobs" not in data:
                data["mind_map_jobs"] = []
                needs_save = True
            if "quiz_jobs" not in data:
                data["quiz_jobs"] = []
                needs_save = True
            if "social_post_jobs" not in data:
                data["social_post_jobs"] = []
                needs_save = True
            # Persist the migration if we added missing keys
            if needs_save:
                save_index(project_id, data)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return default_index


def save_index(project_id: str, index_data: Dict[str, Any]) -> None:
    """Save the studio index for a project."""
    index_path = _get_index_path(project_id)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    index_data["last_updated"] = datetime.now().isoformat()
    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=2)


# =============================================================================
# Audio Job Management
# =============================================================================

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


# =============================================================================
# Ad Creative Job Management
# =============================================================================

def create_ad_job(
    project_id: str,
    job_id: str,
    product_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new ad creative generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        product_name: Product to create ads for
        direction: User's direction for the ads

    Returns:
        The created job record
    """
    job = {
        "id": job_id,
        "product_name": product_name,
        "direction": direction,
        "status": "pending",
        "progress": "Initializing...",
        "error": None,
        "images": [],
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    index["ad_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_ad_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update an ad job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["ad_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["ad_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_ad_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get an ad job by ID."""
    index = load_index(project_id)

    for job in index["ad_jobs"]:
        if job["id"] == job_id:
            return job

    return None


def list_ad_jobs(project_id: str) -> List[Dict[str, Any]]:
    """
    List ad jobs.

    Args:
        project_id: The project UUID

    Returns:
        List of ad jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("ad_jobs", [])

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


# =============================================================================
# Flash Card Job Management
# =============================================================================

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


# =============================================================================
# Mind Map Job Management
# =============================================================================

def create_mind_map_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new mind map generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the mind map

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
        "nodes": [],
        "topic_summary": None,
        "node_count": 0,
        "generation_time_seconds": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    print(f"[StudioIndex] Creating mind map job {job_id}, existing jobs: {len(index.get('mind_map_jobs', []))}")
    index["mind_map_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['mind_map_jobs'])} mind map jobs")

    return job


def update_mind_map_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a mind map job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["mind_map_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["mind_map_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_mind_map_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a mind map job by ID."""
    index = load_index(project_id)
    jobs = index.get("mind_map_jobs", [])
    print(f"[StudioIndex] Looking for mind map job {job_id}, found {len(jobs)} jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Mind map job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_mind_map_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List mind map jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of mind map jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("mind_map_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_mind_map_job(project_id: str, job_id: str) -> bool:
    """
    Delete a mind map job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["mind_map_jobs"])

    index["mind_map_jobs"] = [j for j in index["mind_map_jobs"] if j["id"] != job_id]

    if len(index["mind_map_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False


# =============================================================================
# Quiz Job Management
# =============================================================================

def create_quiz_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new quiz generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the quiz

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
        "questions": [],
        "topic_summary": None,
        "question_count": 0,
        "generation_time_seconds": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    print(f"[StudioIndex] Creating quiz job {job_id}, existing jobs: {len(index.get('quiz_jobs', []))}")
    index["quiz_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['quiz_jobs'])} quiz jobs")

    return job


def update_quiz_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a quiz job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["quiz_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["quiz_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_quiz_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a quiz job by ID."""
    index = load_index(project_id)
    jobs = index.get("quiz_jobs", [])
    print(f"[StudioIndex] Looking for quiz job {job_id}, found {len(jobs)} jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Quiz job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_quiz_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List quiz jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of quiz jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("quiz_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_quiz_job(project_id: str, job_id: str) -> bool:
    """
    Delete a quiz job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["quiz_jobs"])

    index["quiz_jobs"] = [j for j in index["quiz_jobs"] if j["id"] != job_id]

    if len(index["quiz_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False


# =============================================================================
# Social Post Job Management
# =============================================================================

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
