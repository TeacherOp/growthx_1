"""
Studio Jobs Package - Individual job management modules.

Educational Note: Each job type (audio, video, presentation, etc.) has its own
module for better organization and maintainability. All modules import the core
load_index/save_index functions from the parent studio_index_service.

This __init__.py re-exports all job functions for backward compatibility.
"""

# Audio Jobs
from .audio_jobs import (
    create_audio_job,
    update_audio_job,
    get_audio_job,
    list_audio_jobs,
    delete_audio_job,
)

# Video Jobs
from .video_jobs import (
    create_video_job,
    update_video_job,
    get_video_job,
    list_video_jobs,
    delete_video_job,
)

# Ad Jobs
from .ad_jobs import (
    create_ad_job,
    update_ad_job,
    get_ad_job,
    list_ad_jobs,
)

# Flash Card Jobs
from .flash_card_jobs import (
    create_flash_card_job,
    update_flash_card_job,
    get_flash_card_job,
    list_flash_card_jobs,
    delete_flash_card_job,
)

# Mind Map Jobs
from .mind_map_jobs import (
    create_mind_map_job,
    update_mind_map_job,
    get_mind_map_job,
    list_mind_map_jobs,
    delete_mind_map_job,
)

# Quiz Jobs
from .quiz_jobs import (
    create_quiz_job,
    update_quiz_job,
    get_quiz_job,
    list_quiz_jobs,
    delete_quiz_job,
)

# Social Post Jobs
from .social_post_jobs import (
    create_social_post_job,
    update_social_post_job,
    get_social_post_job,
    list_social_post_jobs,
    delete_social_post_job,
)

# Infographic Jobs
from .infographic_jobs import (
    create_infographic_job,
    update_infographic_job,
    get_infographic_job,
    list_infographic_jobs,
    delete_infographic_job,
)

# Email Jobs
from .email_jobs import (
    create_email_job,
    update_email_job,
    get_email_job,
    list_email_jobs,
    delete_email_job,
)

# Website Jobs
from .website_jobs import (
    create_website_job,
    update_website_job,
    get_website_job,
    list_website_jobs,
    delete_website_job,
)

# Component Jobs
from .component_jobs import (
    create_component_job,
    update_component_job,
    get_component_job,
    list_component_jobs,
    delete_component_job,
)

# Flow Diagram Jobs
from .flow_diagram_jobs import (
    create_flow_diagram_job,
    update_flow_diagram_job,
    get_flow_diagram_job,
    list_flow_diagram_jobs,
    delete_flow_diagram_job,
)

# Wireframe Jobs
from .wireframe_jobs import (
    create_wireframe_job,
    update_wireframe_job,
    get_wireframe_job,
    list_wireframe_jobs,
    delete_wireframe_job,
)

# Presentation Jobs
from .presentation_jobs import (
    create_presentation_job,
    update_presentation_job,
    get_presentation_job,
    list_presentation_jobs,
    delete_presentation_job,
)

# PRD Jobs
from .prd_jobs import (
    create_prd_job,
    update_prd_job,
    get_prd_job,
    list_prd_jobs,
    delete_prd_job,
)

# Marketing Strategy Jobs
from .marketing_strategy_jobs import (
    create_marketing_strategy_job,
    update_marketing_strategy_job,
    get_marketing_strategy_job,
    list_marketing_strategy_jobs,
    delete_marketing_strategy_job,
)

# Blog Jobs
from .blog_jobs import (
    create_blog_job,
    update_blog_job,
    get_blog_job,
    list_blog_jobs,
    delete_blog_job,
)

# Business Report Jobs
from .business_report_jobs import (
    create_business_report_job,
    update_business_report_job,
    get_business_report_job,
    list_business_report_jobs,
    delete_business_report_job,
)
