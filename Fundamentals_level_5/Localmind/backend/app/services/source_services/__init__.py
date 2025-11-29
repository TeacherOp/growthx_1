"""
Source Services - Services for managing project sources.

Educational Note: This folder contains services that handle uploading, storing,
processing, and managing source files for projects. Sources are the documents,
images, audio, and data files that users upload to be used as context for AI
conversations.

Folder Structure:
- source_service.py: Main source management (CRUD operations, delegates to modules below)
- source_index_service.py: Index (metadata) CRUD operations for sources_index.json
- source_upload/: Upload handlers for different source types (file, URL, text)
- source_processing/: Processing orchestration and processors for different file types

Processing Pipeline:
1. Upload: source_upload/ modules handle validation and storage
2. Index: source_index_service manages metadata in sources_index.json
3. Process: source_processing/ extracts content, generates embeddings and summaries
"""
from app.services.source_services.source_service import source_service, SourceService
from app.services.source_services import source_index_service

__all__ = ["source_service", "SourceService", "source_index_service"]
