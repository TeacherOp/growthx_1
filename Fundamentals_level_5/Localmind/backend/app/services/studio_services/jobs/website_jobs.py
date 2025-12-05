"""
Website Job Management - Tracks website generation jobs.

Educational Note: Website jobs use an AI agent with iterative refinement to
generate multi-page static websites with HTML, CSS, and JavaScript.
Unlike email templates (single file), websites have multiple files created iteratively.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


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
        "status": "pending",  # pending -> processing -> ready | error
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
