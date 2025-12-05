"""
Presentation Job Management - Tracks presentation generation jobs.

Educational Note: Presentations are generated as HTML slides that are
screenshotted at 1920x1080 and exported to PPTX format using python-pptx.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_presentation_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new presentation generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the presentation

    Returns:
        The created job record
    """
    job = {
        "id": job_id,
        "source_id": source_id,
        "source_name": source_name,
        "direction": direction,
        "status": "pending",  # pending -> processing -> ready | error
        "status_message": "Initializing...",
        "error_message": None,

        # Plan
        "presentation_title": None,
        "presentation_type": None,  # business, educational, pitch, report, etc.
        "target_audience": None,
        "planned_slides": [],  # [{slide_number, slide_type, title, key_points}]
        "design_system": None,  # {primary_color, secondary_color, etc.}
        "style_notes": None,

        # Generated content
        "files": [],  # [base-styles.css, slide_01.html, slide_02.html, ...]
        "slide_files": [],  # Just the slide HTML files in order
        "slides_created": 0,  # Number of slides created
        "slides_metadata": [],  # [{filename, title, type}]
        "total_slides": 0,
        "summary": None,
        "design_notes": None,

        # Export
        "screenshots": [],  # [{slide_file, screenshot_file}]
        "pptx_file": None,  # Path to generated PPTX
        "pptx_filename": None,
        "export_status": None,  # pending -> exporting -> ready | error

        # URLs
        "preview_url": None,
        "download_url": None,

        # Metadata
        "iterations": None,
        "input_tokens": None,
        "output_tokens": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    index["presentation_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_presentation_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a presentation job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["presentation_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["presentation_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_presentation_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a presentation job by ID."""
    index = load_index(project_id)
    jobs = index.get("presentation_jobs", [])

    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def list_presentation_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List presentation jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of presentation jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("presentation_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_presentation_job(project_id: str, job_id: str) -> bool:
    """
    Delete a presentation job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["presentation_jobs"])

    index["presentation_jobs"] = [j for j in index["presentation_jobs"] if j["id"] != job_id]

    if len(index["presentation_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
