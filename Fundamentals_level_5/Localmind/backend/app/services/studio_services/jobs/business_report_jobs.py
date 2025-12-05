"""
Business Report Job Management - Tracks business report generation jobs.

Educational Note: Business reports combine AI-generated content with data analysis.
This job tracker handles reports that may include:
- Written analysis and insights
- Charts/graphs from CSV data analysis (via csv_analyzer_agent)
- Context from multiple source types
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_business_report_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str,
    report_type: str,
    csv_source_ids: List[str],
    context_source_ids: List[str],
    focus_areas: List[str]
) -> Dict[str, Any]:
    """
    Create a new business report generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Primary source for the signal
        source_name: Name of the primary source
        direction: User's direction for the report
        report_type: Type of report (executive_summary, financial_report, etc.)
        csv_source_ids: List of CSV source IDs to analyze
        context_source_ids: List of non-CSV source IDs for context
        focus_areas: Optional list of focus areas/topics

    Returns:
        The created job record
    """
    job = {
        "id": job_id,
        "source_id": source_id,
        "source_name": source_name,
        "direction": direction,
        "report_type": report_type,
        "csv_source_ids": csv_source_ids,
        "context_source_ids": context_source_ids,
        "focus_areas": focus_areas,
        "status": "pending",
        "status_message": "Initializing...",
        "error_message": None,
        # Report plan fields
        "title": None,
        "executive_summary": None,
        "sections": [],  # List of section objects
        # Data analysis tracking
        "analyses": [],  # List of {query, summary, chart_paths}
        "charts": [],  # List of {filename, title, description, url}
        # Generated content
        "markdown_file": None,
        "markdown_url": None,
        "preview_url": None,
        "word_count": None,
        # Metadata
        "iterations": None,
        "input_tokens": None,
        "output_tokens": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    index = load_index(project_id)
    index["business_report_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_business_report_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a business report job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["business_report_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["business_report_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_business_report_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a business report job by ID."""
    index = load_index(project_id)
    jobs = index.get("business_report_jobs", [])

    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def list_business_report_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List business report jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of business report jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("business_report_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_business_report_job(project_id: str, job_id: str) -> bool:
    """
    Delete a business report job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["business_report_jobs"])

    index["business_report_jobs"] = [j for j in index["business_report_jobs"] if j["id"] != job_id]

    if len(index["business_report_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
