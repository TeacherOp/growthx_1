"""
Studio Services - Services for studio features (audio overview, deep dive, etc.).

Educational Note: This folder contains services that handle studio features
like audio overview generation, deep dive conversations, and other interactive
content creation features.

Current Services:
- audio_overview_service: Generates audio overviews from source content
  Uses agentic loop to read content and generate TTS-optimized scripts
- studio_index_service: Tracks studio generation jobs (status, progress)

Planned Services:
- Deep dive conversation mode
- Interactive Q&A features
"""
from app.services.studio_services import studio_index_service
from app.services.studio_services.audio_overview_service import audio_overview_service

__all__ = ["audio_overview_service", "studio_index_service"]
