"""
Ad Creative Job Management - Tracks ad image generation jobs.

Educational Note: Ad jobs generate marketing creatives using AI image generation.
Creates multiple ad variations for products based on source content.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


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
