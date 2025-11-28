"""
Source Service - Business logic for managing project sources.

Educational Note: This service handles uploading, storing, and managing
source files for projects. Sources are the documents, images, audio,
and data files that users upload to be used as context for AI conversations.

Storage Structure:
    data/projects/{project_id}/
    ├── sources/
    │   ├── sources_index.json    # Metadata index for all sources
    │   ├── raw/                  # Raw uploaded files
    │   │   ├── {source_id}.pdf
    │   │   ├── {source_id}.txt
    │   │   └── ...
    │   ├── processed/            # Extracted/processed text content
    │   │   ├── {source_id}.txt
    │   │   └── ...
    │   └── chunks/               # Chunked text for embeddings
    │       └── {source_id}/
    │           ├── {source_id}_chunk_1.txt
    │           └── ...

Responsibilities:
    - Path and directory management
    - Index (metadata) management
    - CRUD operations for sources
    - Source uploads (file, URL, text)

Processing is handled by source_processing_service.py
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from werkzeug.datastructures import FileStorage

from config import Config
from app.services.task_service import task_service
from app.utils.file_utils import (
    ALLOWED_EXTENSIONS,
    is_allowed_file,
    get_file_info,
    validate_file_size,
)


class SourceService:
    """
    Service class for managing project sources.

    Educational Note: Sources are raw files uploaded by users. This service
    handles storage and metadata management. Processing (text extraction,
    embedding generation) is handled by source_processing_service.
    """

    def __init__(self):
        """Initialize the source service with the projects directory."""
        self.projects_dir = Config.PROJECTS_DIR

    # =========================================================================
    # Path Management
    # =========================================================================

    def _get_sources_dir(self, project_id: str) -> Path:
        """Get the sources directory for a project."""
        return self.projects_dir / project_id / "sources"

    def _get_raw_dir(self, project_id: str) -> Path:
        """Get the raw files directory for a project."""
        return self._get_sources_dir(project_id) / "raw"

    def _get_processed_dir(self, project_id: str) -> Path:
        """
        Get the processed files directory for a project.

        Educational Note: Processed files contain extracted text content
        from PDFs, images (OCR), etc. This is the content that will be
        used by the AI for context.
        """
        return self._get_sources_dir(project_id) / "processed"

    def _get_chunks_dir(self, project_id: str) -> Path:
        """
        Get the chunks directory for a project.

        Educational Note: Chunks are individual .txt files created when
        a source is embedded. Each chunk represents one page of a document.
        When Pinecone returns search results, we load text from these files.
        """
        return self._get_sources_dir(project_id) / "chunks"

    def _get_index_path(self, project_id: str) -> Path:
        """Get the sources index file path for a project."""
        return self._get_sources_dir(project_id) / "sources_index.json"

    def _ensure_directories(self, project_id: str) -> None:
        """
        Ensure source directories exist for a project.

        Educational Note: We create the directory structure lazily
        when the first source is uploaded to a project.
        """
        sources_dir = self._get_sources_dir(project_id)
        raw_dir = self._get_raw_dir(project_id)
        processed_dir = self._get_processed_dir(project_id)
        chunks_dir = self._get_chunks_dir(project_id)

        sources_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        chunks_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Index Management
    # =========================================================================

    def _load_index(self, project_id: str) -> Dict[str, Any]:
        """
        Load the sources index for a project.

        Returns empty structure if index doesn't exist.
        """
        index_path = self._get_index_path(project_id)

        if not index_path.exists():
            return {
                "sources": [],
                "last_updated": datetime.now().isoformat()
            }

        try:
            with open(index_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "sources": [],
                "last_updated": datetime.now().isoformat()
            }

    def _save_index(self, project_id: str, index_data: Dict[str, Any]) -> None:
        """Save the sources index for a project."""
        self._ensure_directories(project_id)
        index_path = self._get_index_path(project_id)

        index_data["last_updated"] = datetime.now().isoformat()
        with open(index_path, 'w') as f:
            json.dump(index_data, f, indent=2)

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def list_sources(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all sources for a project.

        Args:
            project_id: The project UUID

        Returns:
            List of source metadata dictionaries
        """
        index = self._load_index(project_id)
        # Sort by created_at, most recent first
        sources = sorted(
            index["sources"],
            key=lambda s: s.get("created_at", ""),
            reverse=True
        )
        return sources

    def get_source(self, project_id: str, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific source's metadata.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Source metadata or None if not found
        """
        index = self._load_index(project_id)

        for source in index["sources"]:
            if source["id"] == source_id:
                return source

        return None

    def get_source_file_path(self, project_id: str, source_id: str) -> Optional[Path]:
        """
        Get the file path for a source's raw file.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Path to the raw file or None if not found
        """
        source = self.get_source(project_id, source_id)
        if not source:
            return None

        file_path = self._get_raw_dir(project_id) / source["stored_filename"]
        if file_path.exists():
            return file_path

        return None

    def update_source(
        self,
        project_id: str,
        source_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        active: Optional[bool] = None,
        processing_info: Optional[Dict[str, Any]] = None,
        embedding_info: Optional[Dict[str, Any]] = None,
        summary_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a source's metadata.

        Args:
            project_id: The project UUID
            source_id: The source UUID
            name: New display name (optional)
            description: New description (optional)
            status: New status (optional)
            active: Whether source is included in chat context (optional)
            processing_info: Processing details (optional)
            embedding_info: Embedding details (optional)
            summary_info: Summary details (optional)

        Returns:
            Updated source metadata or None if not found
        """
        index = self._load_index(project_id)

        for i, source in enumerate(index["sources"]):
            if source["id"] == source_id:
                # Update fields if provided
                if name is not None:
                    source["name"] = name
                if description is not None:
                    source["description"] = description
                if status is not None:
                    source["status"] = status
                    # Auto-activate when status becomes ready
                    if status == "ready":
                        source["active"] = True
                if active is not None:
                    source["active"] = active
                if processing_info is not None:
                    source["processing_info"] = processing_info
                if embedding_info is not None:
                    source["embedding_info"] = embedding_info
                if summary_info is not None:
                    source["summary_info"] = summary_info

                source["updated_at"] = datetime.now().isoformat()
                index["sources"][i] = source

                self._save_index(project_id, index)
                print(f"Updated source: {source_id}")

                return source

        return None

    def delete_source(self, project_id: str, source_id: str) -> bool:
        """
        Delete a source, its raw file, processed content, and embeddings.

        Educational Note: When deleting a source, we clean up:
        1. Raw file (original upload)
        2. Processed file (extracted text)
        3. Chunk files (individual page files)
        4. Pinecone vectors (via embedding_workflow_service)

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            True if deleted, False if not found
        """
        source = self.get_source(project_id, source_id)
        if not source:
            return False

        # Delete embeddings and chunk files (if any)
        if source.get("embedding_info", {}).get("is_embedded"):
            try:
                from app.services.embedding_workflow_service import embedding_workflow_service
                chunks_dir = self._get_chunks_dir(project_id)
                embedding_workflow_service.delete_embeddings(
                    project_id=project_id,
                    source_id=source_id,
                    chunks_dir=chunks_dir
                )
            except Exception as e:
                print(f"Error deleting embeddings for {source_id}: {e}")

        # Delete the raw file
        file_path = self._get_raw_dir(project_id) / source["stored_filename"]
        if file_path.exists():
            file_path.unlink()

        # Delete the processed file (if exists)
        processed_path = self._get_processed_dir(project_id) / f"{source_id}.txt"
        if processed_path.exists():
            processed_path.unlink()

        # Remove from index
        index = self._load_index(project_id)
        index["sources"] = [s for s in index["sources"] if s["id"] != source_id]
        self._save_index(project_id, index)

        print(f"Deleted source: {source_id}")

        return True

    def get_sources_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get a summary of sources for a project.

        Educational Note: This provides aggregate stats about sources,
        useful for displaying in the UI.

        Returns:
            Dictionary with source counts by category and total size
        """
        sources = self.list_sources(project_id)

        summary = {
            "total_count": len(sources),
            "total_size": sum(s.get("file_size", 0) for s in sources),
            "by_category": {},
            "by_status": {}
        }

        for source in sources:
            # Count by category
            category = source.get("category", "unknown")
            if category not in summary["by_category"]:
                summary["by_category"][category] = 0
            summary["by_category"][category] += 1

            # Count by status
            status = source.get("status", "unknown")
            if status not in summary["by_status"]:
                summary["by_status"][status] = 0
            summary["by_status"][status] += 1

        return summary

    def get_allowed_extensions(self) -> dict:
        """
        Get the allowed file extensions and their categories.

        Returns:
            Dictionary mapping extensions to categories
        """
        return ALLOWED_EXTENSIONS.copy()

    # =========================================================================
    # Source Upload/Creation
    # =========================================================================

    def upload_source(
        self,
        project_id: str,
        file: FileStorage,
        name: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Upload a new source file to a project.

        Args:
            project_id: The project UUID
            file: The uploaded file (Flask FileStorage)
            name: Optional display name (defaults to original filename)
            description: Optional description of the source

        Returns:
            Source metadata dictionary

        Raises:
            ValueError: If file type is not allowed or file is empty
        """
        # Validate file
        if not file or not file.filename:
            raise ValueError("No file provided")

        original_filename = file.filename
        if not is_allowed_file(original_filename):
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS.keys()))
            raise ValueError(f"File type not allowed. Allowed types: {allowed}")

        # Get file info
        ext, category, mime_type = get_file_info(original_filename)

        # Generate source ID and paths
        source_id = str(uuid.uuid4())
        stored_filename = f"{source_id}{ext}"
        raw_dir = self._get_raw_dir(project_id)

        # Ensure directories exist
        self._ensure_directories(project_id)

        # Save the file
        file_path = raw_dir / stored_filename
        file.save(str(file_path))

        # Get file size
        file_size = file_path.stat().st_size

        # Validate file size (e.g., images have 5MB limit)
        size_error = validate_file_size(original_filename, file_size)
        if size_error:
            # Delete the saved file and raise error
            file_path.unlink()
            raise ValueError(size_error)

        # Create source metadata
        timestamp = datetime.now().isoformat()
        source_metadata = {
            "id": source_id,
            "project_id": project_id,
            "name": name or original_filename,
            "original_filename": original_filename,
            "description": description,
            "category": category,
            "mime_type": mime_type,
            "file_extension": ext,
            "file_size": file_size,
            "stored_filename": stored_filename,
            "status": "uploaded",
            "active": False,
            "processing_info": None,
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Uploaded source: {source_metadata['name']} ({source_id})")

        # Submit processing as a background task
        # Educational Note: Import here to avoid circular imports at module load
        from app.services.source_processing_service import source_processing_service

        task_service.submit_task(
            "source_processing",
            source_id,
            source_processing_service.process_source,
            project_id,
            source_id
        )

        return source_metadata

    def create_source_from_file(
        self,
        project_id: str,
        file_path: Path,
        name: str,
        original_filename: str,
        category: str,
        mime_type: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a source entry from an already-saved file.

        Educational Note: This is used when a file is downloaded/saved externally
        (e.g., from Google Drive) and we need to create the source index entry.
        The file should already exist at the given path.

        Args:
            project_id: The project UUID
            file_path: Path where the file is already saved
            name: Display name for the source
            original_filename: Original filename (used for extension)
            category: Source category (document, image, audio, etc.)
            mime_type: MIME type of the file
            description: Optional description

        Returns:
            Source metadata dictionary
        """
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        # Get extension from stored filename
        ext = file_path.suffix.lower()
        source_id = file_path.stem  # UUID is the filename without extension

        # Get file size
        file_size = file_path.stat().st_size

        # Create source metadata
        timestamp = datetime.now().isoformat()
        source_metadata = {
            "id": source_id,
            "project_id": project_id,
            "name": name,
            "original_filename": original_filename,
            "description": description,
            "category": category,
            "mime_type": mime_type,
            "file_extension": ext,
            "file_size": file_size,
            "stored_filename": file_path.name,
            "status": "uploaded",
            "active": False,
            "processing_info": None,
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Created source from file: {name} ({source_id})")

        # Submit processing as a background task
        from app.services.source_processing_service import source_processing_service

        task_service.submit_task(
            "source_processing",
            source_id,
            source_processing_service.process_source,
            project_id,
            source_id
        )

        return source_metadata

    def add_url_source(
        self,
        project_id: str,
        url: str,
        name: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Add a URL source (website or YouTube link) to a project.

        Educational Note: URLs are stored as .link files containing JSON
        with the URL and metadata. The actual content fetching/processing
        happens in a separate processing step.

        Args:
            project_id: The project UUID
            url: The URL to store
            name: Optional display name (defaults to URL)
            description: Optional description

        Returns:
            Source metadata dictionary
        """
        import re

        # Basic URL validation
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        url = url.strip()

        # Check if it looks like a URL
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            raise ValueError("Invalid URL format. Must start with http:// or https://")

        # Detect if it's a YouTube URL
        is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
        link_type = 'youtube' if is_youtube else 'website'

        # Generate source ID and paths
        source_id = str(uuid.uuid4())
        stored_filename = f"{source_id}.link"
        raw_dir = self._get_raw_dir(project_id)

        # Ensure directories exist
        self._ensure_directories(project_id)

        # Create link file with URL data
        link_data = {
            "url": url,
            "type": link_type,
            "fetched": False,
            "fetched_at": None
        }

        file_path = raw_dir / stored_filename
        with open(file_path, 'w') as f:
            json.dump(link_data, f, indent=2)

        file_size = file_path.stat().st_size

        # Create source metadata
        timestamp = datetime.now().isoformat()
        source_metadata = {
            "id": source_id,
            "project_id": project_id,
            "name": name or url,
            "original_filename": url,
            "description": description,
            "category": "link",
            "mime_type": "application/json",
            "file_extension": ".link",
            "file_size": file_size,
            "stored_filename": stored_filename,
            "status": "uploaded",
            "active": False,
            "processing_info": {"link_type": link_type},
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Added URL source: {url} ({source_id})")

        # Submit background processing task
        # Educational Note: URL content extraction runs in background thread
        # so it doesn't block the API response
        from app.services.task_service import task_service
        from app.services.source_processing_service import source_processing_service

        task_service.submit_task(
            "source_processing",
            source_id,
            source_processing_service.process_source,
            project_id,
            source_id
        )

        return source_metadata

    def add_text_source(
        self,
        project_id: str,
        content: str,
        name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Add a pasted text source to a project.

        Educational Note: Pasted text is stored as a .txt file.
        This is the simplest source type - the raw content IS the processed content.

        Args:
            project_id: The project UUID
            content: The pasted text content
            name: Display name for the source (required)
            description: Optional description

        Returns:
            Source metadata dictionary
        """
        # Validate inputs
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        if not name or not name.strip():
            raise ValueError("Name is required for pasted text")

        content = content.strip()
        name = name.strip()

        # Generate source ID and paths
        source_id = str(uuid.uuid4())
        stored_filename = f"{source_id}.txt"
        raw_dir = self._get_raw_dir(project_id)

        # Ensure directories exist
        self._ensure_directories(project_id)

        # Save the text content
        file_path = raw_dir / stored_filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        file_size = file_path.stat().st_size

        # Create source metadata
        timestamp = datetime.now().isoformat()
        source_metadata = {
            "id": source_id,
            "project_id": project_id,
            "name": name,
            "original_filename": f"{name}.txt",
            "description": description,
            "category": "document",
            "mime_type": "text/plain",
            "file_extension": ".txt",
            "file_size": file_size,
            "stored_filename": stored_filename,
            "status": "uploaded",
            "active": False,
            "processing_info": {"source_type": "pasted_text"},
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Added text source: {name} ({source_id})")

        # Submit processing as background task
        from app.services.source_processing_service import source_processing_service

        task_service.submit_task(
            "source_processing",
            source_id,
            source_processing_service.process_source,
            project_id,
            source_id
        )

        return source_metadata

    # =========================================================================
    # Processing Delegation (thin wrappers)
    # =========================================================================

    def cancel_processing(self, project_id: str, source_id: str) -> bool:
        """
        Cancel processing for a source.

        Delegates to source_processing_service.
        """
        from app.services.source_processing_service import source_processing_service
        return source_processing_service.cancel_processing(project_id, source_id)

    def retry_processing(self, project_id: str, source_id: str) -> Dict[str, Any]:
        """
        Retry processing for a source that failed or was cancelled.

        Delegates to source_processing_service.
        """
        from app.services.source_processing_service import source_processing_service
        return source_processing_service.retry_processing(project_id, source_id)


# Singleton instance
source_service = SourceService()
