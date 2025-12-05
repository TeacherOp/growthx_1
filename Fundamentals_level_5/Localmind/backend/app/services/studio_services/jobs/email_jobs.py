"""
Email Template Job Management - Tracks email template generation jobs.

Educational Note: Email jobs use an AI agent with iterative refinement to
generate responsive HTML email templates with AI-generated images.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


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
