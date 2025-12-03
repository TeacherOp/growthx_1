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
        "infographic_jobs": [],
        "email_jobs": [],
        "website_jobs": [],
        "component_jobs": [],
        "video_jobs": [],
        "flow_diagram_jobs": [],
        "wireframe_jobs": [],
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
            if "infographic_jobs" not in data:
                data["infographic_jobs"] = []
                needs_save = True
            if "email_jobs" not in data:
                data["email_jobs"] = []
                needs_save = True
            if "website_jobs" not in data:
                data["website_jobs"] = []
                needs_save = True
            if "component_jobs" not in data:
                data["component_jobs"] = []
                needs_save = True
            if "video_jobs" not in data:
                data["video_jobs"] = []
                needs_save = True
            if "flow_diagram_jobs" not in data:
                data["flow_diagram_jobs"] = []
                needs_save = True
            if "wireframe_jobs" not in data:
                data["wireframe_jobs"] = []
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


# =============================================================================
# Infographic Job Management
# =============================================================================

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


# =============================================================================
# Email Template Job Management
# =============================================================================

def create_email_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new email template generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the template

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
        # Template plan fields
        "template_name": None,
        "template_type": None,
        "color_scheme": None,
        "sections": [],
        "layout_notes": None,
        # Generated content
        "images": [],  # List of {section_name, filename, placeholder, url}
        "html_file": None,
        "html_url": None,
        "preview_url": None,
        "subject_line": None,
        "preheader_text": None,
        # Metadata
        "iterations": None,
        "input_tokens": None,
        "output_tokens": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    index["email_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_email_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update an email job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["email_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["email_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_email_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get an email job by ID."""
    index = load_index(project_id)
    jobs = index.get("email_jobs", [])

    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def list_email_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List email jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of email jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("email_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_email_job(project_id: str, job_id: str) -> bool:
    """
    Delete an email job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["email_jobs"])

    index["email_jobs"] = [j for j in index["email_jobs"] if j["id"] != job_id]

    if len(index["email_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False


# =============================================================================
# Website Jobs (Website Generator)
# =============================================================================

def create_website_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> None:
    """
    Create a new website generation job in the index.

    Educational Note: Tracks website generation with multi-file support.
    Unlike email templates (single HTML file), websites have multiple files
    (HTML pages, CSS, JS) that are created iteratively.
    """
    index = load_index(project_id)

    job = {
        "id": job_id,
        "source_id": source_id,
        "source_name": source_name,
        "direction": direction,
        "status": "pending",  # pending → processing → ready | error
        "status_message": "Initializing...",
        "error_message": None,

        # Plan
        "site_type": None,  # portfolio, business, blog, landing, corporate, etc.
        "site_name": None,
        "pages": [],  # [{filename, page_title, description}]
        "features": [],  # [animations_scroll, gallery_grid, contact_form, etc.]
        "design_system": None,  # {primary_color, secondary_color, etc.}
        "navigation_style": None,  # fixed, sticky, static
        "images_needed": [],  # [{purpose, description, aspect_ratio}]
        "layout_notes": None,

        # Generated content
        "images": [],  # [{purpose, filename, placeholder, url}]
        "files": [],  # [index.html, about.html, styles.css, script.js]
        "pages_created": [],  # [index.html, about.html, contact.html, ...]
        "features_implemented": [],  # Actual features implemented
        "cdn_libraries_used": [],  # [Tailwind CSS, Font Awesome, etc.]
        "summary": None,

        # URLs
        "preview_url": None,  # URL to preview website (serves index.html)
        "download_url": None,  # URL to download ZIP

        # Metadata
        "iterations": None,
        "input_tokens": None,
        "output_tokens": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index["website_jobs"].append(job)
    save_index(project_id, index)


def update_website_job(
    project_id: str,
    job_id: str,
    **updates
) -> None:
    """
    Update a website job with new information.

    Educational Note: Flexible updates for any job fields during
    the agent's iterative workflow.
    """
    index = load_index(project_id)

    for job in index["website_jobs"]:
        if job["id"] == job_id:
            # Update all provided fields
            for key, value in updates.items():
                if key in job:
                    job[key] = value
            break

    save_index(project_id, index)


def get_website_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific website job by ID."""
    index = load_index(project_id)
    jobs = index.get("website_jobs", [])

    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def list_website_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List website jobs, optionally filtered by source_id.

    Returns jobs sorted by created_at descending (newest first).
    """
    index = load_index(project_id)
    jobs = index.get("website_jobs", [])

    # Filter by source if provided
    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_website_job(project_id: str, job_id: str) -> bool:
    """
    Delete a website job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["website_jobs"])

    index["website_jobs"] = [j for j in index["website_jobs"] if j["id"] != job_id]

    if len(index["website_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False


# =============================================================================
# Component Jobs (UI Component Generator)
# =============================================================================

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


# =============================================================================
# Video Job Management
# =============================================================================

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


# =============================================================================
# Flow Diagram Job Management
# =============================================================================

def create_flow_diagram_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new flow diagram generation job.

    Educational Note: Flow diagrams use Mermaid.js syntax which is rendered
    directly by the frontend Mermaid library, unlike mind maps which use
    a custom node structure with React Flow.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the diagram

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
        "mermaid_syntax": None,
        "diagram_type": None,
        "title": None,
        "description": None,
        "generation_time_seconds": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    print(f"[StudioIndex] Creating flow diagram job {job_id}, existing jobs: {len(index.get('flow_diagram_jobs', []))}")
    index["flow_diagram_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['flow_diagram_jobs'])} flow diagram jobs")

    return job


def update_flow_diagram_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a flow diagram job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["flow_diagram_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["flow_diagram_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_flow_diagram_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a flow diagram job by ID."""
    index = load_index(project_id)
    jobs = index.get("flow_diagram_jobs", [])
    print(f"[StudioIndex] Looking for flow diagram job {job_id}, found {len(jobs)} jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Flow diagram job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_flow_diagram_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List flow diagram jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of flow diagram jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("flow_diagram_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_flow_diagram_job(project_id: str, job_id: str) -> bool:
    """
    Delete a flow diagram job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["flow_diagram_jobs"])

    index["flow_diagram_jobs"] = [j for j in index["flow_diagram_jobs"] if j["id"] != job_id]

    if len(index["flow_diagram_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False


# =============================================================================
# Wireframe Job Management
# =============================================================================

def create_wireframe_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new wireframe generation job.

    Educational Note: Wireframes use Excalidraw elements to create
    hand-drawn style UI prototypes, perfect for early-stage design.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the wireframe

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
        "title": None,
        "description": None,
        "elements": [],
        "canvas_width": 1200,
        "canvas_height": 800,
        "element_count": 0,
        "generation_time_seconds": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    print(f"[StudioIndex] Creating wireframe job {job_id}, existing jobs: {len(index.get('wireframe_jobs', []))}")
    index["wireframe_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['wireframe_jobs'])} wireframe jobs")

    return job


def update_wireframe_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a wireframe job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["wireframe_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["wireframe_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_wireframe_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a wireframe job by ID."""
    index = load_index(project_id)
    jobs = index.get("wireframe_jobs", [])
    print(f"[StudioIndex] Looking for wireframe job {job_id}, found {len(jobs)} jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Wireframe job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_wireframe_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List wireframe jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of wireframe jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("wireframe_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_wireframe_job(project_id: str, job_id: str) -> bool:
    """
    Delete a wireframe job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["wireframe_jobs"])

    index["wireframe_jobs"] = [j for j in index["wireframe_jobs"] if j["id"] != job_id]

    if len(index["wireframe_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
