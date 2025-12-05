"""
Blog Post Job Management - Tracks blog post generation jobs.

Educational Note: Blog jobs use an AI agent with image generation capabilities
to create comprehensive, SEO-optimized blog posts in Markdown format.
The agent can generate images to embed within the blog content.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.services.studio_services.studio_index_service import load_index, save_index


def create_blog_job(
    project_id: str,
    job_id: str,
    source_id: str,
    source_name: str,
    direction: str,
    target_keyword: str,
    blog_type: str
) -> Dict[str, Any]:
    """
    Create a new blog post generation job.

    Args:
        project_id: The project UUID
        job_id: Unique job identifier
        source_id: Source being processed
        source_name: Name of the source
        direction: User's direction for the blog
        target_keyword: SEO keyword/phrase to target
        blog_type: Category of blog (case_study, listicle, how_to_guide, etc.)

    Returns:
        The created job record
    """
    job = {
        "id": job_id,
        "source_id": source_id,
        "source_name": source_name,
        "direction": direction,
        "target_keyword": target_keyword,
        "blog_type": blog_type,
        "status": "pending",
        "status_message": "Initializing...",
        "error_message": None,
        # Blog plan fields
        "title": None,
        "meta_description": None,
        "outline": [],  # List of section headings
        "target_word_count": 3000,
        "tone": None,
        # Generated content
        "images": [],  # List of {purpose, filename, placeholder, url}
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
    index["blog_jobs"].append(job)
    save_index(project_id, index)

    return job


def update_blog_job(
    project_id: str,
    job_id: str,
    **updates
) -> Optional[Dict[str, Any]]:
    """
    Update a blog job's fields.

    Args:
        project_id: The project UUID
        job_id: The job ID to update
        **updates: Fields to update

    Returns:
        Updated job record or None if not found
    """
    index = load_index(project_id)

    for i, job in enumerate(index["blog_jobs"]):
        if job["id"] == job_id:
            for key, value in updates.items():
                if value is not None:
                    job[key] = value
            job["updated_at"] = datetime.now().isoformat()
            index["blog_jobs"][i] = job
            save_index(project_id, index)
            return job

    return None


def get_blog_job(project_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a blog job by ID."""
    index = load_index(project_id)
    jobs = index.get("blog_jobs", [])

    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def list_blog_jobs(project_id: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List blog jobs, optionally filtered by source.

    Args:
        project_id: The project UUID
        source_id: Optional source ID to filter by

    Returns:
        List of blog jobs (newest first)
    """
    index = load_index(project_id)
    jobs = index.get("blog_jobs", [])

    if source_id:
        jobs = [j for j in jobs if j.get("source_id") == source_id]

    # Sort by created_at descending
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def delete_blog_job(project_id: str, job_id: str) -> bool:
    """
    Delete a blog job from the index.

    Returns:
        True if job was found and deleted
    """
    index = load_index(project_id)
    original_count = len(index["blog_jobs"])

    index["blog_jobs"] = [j for j in index["blog_jobs"] if j["id"] != job_id]

    if len(index["blog_jobs"]) < original_count:
        save_index(project_id, index)
        return True

    return False
