"""
Marketing Strategy Job Management - Tracks marketing strategy document generation jobs.

Educational Note: Marketing strategy jobs use an agentic loop pattern where Claude:
1. Plans the document structure (sections to write)
2. Writes sections incrementally to a markdown file
3. Signals completion via is_last_section flag

The markdown output can be rendered nicely on frontend and exported to PDF.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_marketing_strategy_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Create a new marketing strategy generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the marketing strategy

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

        # Plan fields
        "document_title": None,
        "product_name": None,
        "target_market": None,
        "planned_sections": [],  # [{section_id, title, description}]
        "planning_notes": None,

        # Progress tracking
        "sections_written": 0,
        "total_sections": 0,
        "current_section": None,

        # Generated content
        "markdown_file": None,
        "markdown_filename": None,

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
    print(f"[StudioIndex] Creating marketing strategy job {job_id}, existing jobs: {len(index.get('marketing_strategy_jobs', []))}")
    index["marketing_strategy_jobs"].append(job)
    save_index(project_id, index)
    print(f"[StudioIndex] Saved index with {len(index['marketing_strategy_jobs'])} marketing strategy jobs")

    return job


def update_marketing_strategy_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a marketing strategy job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["marketing_strategy_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["marketing_strategy_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_marketing_strategy_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a marketing strategy job by ID."""
    index = load_index(project_id)
    jobs = index.get("marketing_strategy_jobs", [])
    print(f"[StudioIndex] Looking for marketing strategy job {job_id}, found {len(jobs)} jobs")

    for job in jobs:
        if job["id"] == job_id:
            return job

    print(f"[StudioIndex] Marketing strategy job {job_id} NOT FOUND. Available IDs: {[j['id'][:8] for j in jobs]}")
    return None


def list_marketing_strategy_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List marketing strategy jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of marketing strategy jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("marketing_strategy_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_marketing_strategy_job(project_id: str, job_id: str) -> bool:
    """
    Delete a marketing strategy job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index.get("marketing_strategy_jobs", []))

    index["marketing_strategy_jobs"] = [j for j in index.get("marketing_strategy_jobs", []) if j["id"] != job_id]

    if len(index["marketing_strategy_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
