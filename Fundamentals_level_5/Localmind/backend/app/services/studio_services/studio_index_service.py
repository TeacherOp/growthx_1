"""
Studio Index Service - Core index management for studio generation jobs.

Educational Note: This service manages a studio_index.json file that tracks
all studio content generation jobs. Similar to sources_index.json but for
generated content.

Job Status Flow:
    pending -> processing -> ready
                          -> error

The frontend polls the status endpoint to know when content is ready.

Architecture:
    This file contains ONLY the core index management functions (load/save).
    Individual job type management (create, update, get, list, delete) is
    organized into separate modules in the jobs/ subfolder:

    jobs/
    ├── audio_jobs.py
    ├── video_jobs.py
    ├── ad_jobs.py
    ├── flash_card_jobs.py
    ├── mind_map_jobs.py
    ├── quiz_jobs.py
    ├── social_post_jobs.py
    ├── infographic_jobs.py
    ├── email_jobs.py
    ├── website_jobs.py
    ├── component_jobs.py
    ├── flow_diagram_jobs.py
    ├── wireframe_jobs.py
    ├── presentation_jobs.py
    ├── prd_jobs.py
    ├── marketing_strategy_jobs.py
    └── business_report_jobs.py
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.utils.path_utils import get_studio_dir


# =============================================================================
# Core Index Management Functions
# =============================================================================

def _get_index_path(project_id: str) -> Path:
    """Get the studio index file path for a project."""
    return get_studio_dir(project_id) / "studio_index.json"


def load_index(project_id: str) -> Dict[str, Any]:
    """
    Load the studio index for a project.

    Returns empty structure if index doesn't exist.
    Handles migration for existing indexes missing new job types.
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
        "presentation_jobs": [],
        "prd_jobs": [],
        "marketing_strategy_jobs": [],
        "blog_jobs": [],
        "business_report_jobs": [],
        "last_updated": datetime.now().isoformat()
    }

    if not index_path.exists():
        return default_index

    try:
        with open(index_path, 'r') as f:
            data = json.load(f)

            # Ensure all job arrays exist (migration for existing indexes)
            needs_save = False
            job_types = [
                "audio_jobs", "ad_jobs", "flash_card_jobs", "mind_map_jobs",
                "quiz_jobs", "social_post_jobs", "infographic_jobs", "email_jobs",
                "website_jobs", "component_jobs", "video_jobs", "flow_diagram_jobs",
                "wireframe_jobs", "presentation_jobs", "prd_jobs", "marketing_strategy_jobs",
                "blog_jobs", "business_report_jobs"
            ]

            for job_type in job_types:
                if job_type not in data:
                    data[job_type] = []
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
# Re-exports for Backward Compatibility
# =============================================================================
# All job-specific functions are now in separate modules under jobs/
# These re-exports ensure existing imports continue to work.

from app.services.studio_services.jobs.audio_jobs import (
    create_audio_job,
    update_audio_job,
    get_audio_job,
    list_audio_jobs,
    delete_audio_job,
)

from app.services.studio_services.jobs.video_jobs import (
    create_video_job,
    update_video_job,
    get_video_job,
    list_video_jobs,
    delete_video_job,
)

from app.services.studio_services.jobs.ad_jobs import (
    create_ad_job,
    update_ad_job,
    get_ad_job,
    list_ad_jobs,
)

from app.services.studio_services.jobs.flash_card_jobs import (
    create_flash_card_job,
    update_flash_card_job,
    get_flash_card_job,
    list_flash_card_jobs,
    delete_flash_card_job,
)

from app.services.studio_services.jobs.mind_map_jobs import (
    create_mind_map_job,
    update_mind_map_job,
    get_mind_map_job,
    list_mind_map_jobs,
    delete_mind_map_job,
)

from app.services.studio_services.jobs.quiz_jobs import (
    create_quiz_job,
    update_quiz_job,
    get_quiz_job,
    list_quiz_jobs,
    delete_quiz_job,
)

from app.services.studio_services.jobs.social_post_jobs import (
    create_social_post_job,
    update_social_post_job,
    get_social_post_job,
    list_social_post_jobs,
    delete_social_post_job,
)

from app.services.studio_services.jobs.infographic_jobs import (
    create_infographic_job,
    update_infographic_job,
    get_infographic_job,
    list_infographic_jobs,
    delete_infographic_job,
)

from app.services.studio_services.jobs.email_jobs import (
    create_email_job,
    update_email_job,
    get_email_job,
    list_email_jobs,
    delete_email_job,
)

from app.services.studio_services.jobs.website_jobs import (
    create_website_job,
    update_website_job,
    get_website_job,
    list_website_jobs,
    delete_website_job,
)

from app.services.studio_services.jobs.component_jobs import (
    create_component_job,
    update_component_job,
    get_component_job,
    list_component_jobs,
    delete_component_job,
)

from app.services.studio_services.jobs.flow_diagram_jobs import (
    create_flow_diagram_job,
    update_flow_diagram_job,
    get_flow_diagram_job,
    list_flow_diagram_jobs,
    delete_flow_diagram_job,
)

from app.services.studio_services.jobs.wireframe_jobs import (
    create_wireframe_job,
    update_wireframe_job,
    get_wireframe_job,
    list_wireframe_jobs,
    delete_wireframe_job,
)

from app.services.studio_services.jobs.presentation_jobs import (
    create_presentation_job,
    update_presentation_job,
    get_presentation_job,
    list_presentation_jobs,
    delete_presentation_job,
)

from app.services.studio_services.jobs.prd_jobs import (
    create_prd_job,
    update_prd_job,
    get_prd_job,
    list_prd_jobs,
    delete_prd_job,
)

from app.services.studio_services.jobs.marketing_strategy_jobs import (
    create_marketing_strategy_job,
    update_marketing_strategy_job,
    get_marketing_strategy_job,
    list_marketing_strategy_jobs,
    delete_marketing_strategy_job,
)

from app.services.studio_services.jobs.blog_jobs import (
    create_blog_job,
    update_blog_job,
    get_blog_job,
    list_blog_jobs,
    delete_blog_job,
)

from app.services.studio_services.jobs.business_report_jobs import (
    create_business_report_job,
    update_business_report_job,
    get_business_report_job,
    list_business_report_jobs,
    delete_business_report_job,
)
