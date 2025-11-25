"""
Source Service - Business logic for managing project sources.

Educational Note: This service handles uploading, storing, and managing
raw source files for projects. Sources are the documents, images, audio,
and data files that users upload to be used as context for AI conversations.

Storage Structure:
    data/projects/{project_id}/
    ├── sources/
    │   ├── sources_index.json    # Metadata index for all sources
    │   └── raw/                  # Raw uploaded files
    │       ├── {source_id}.pdf
    │       ├── {source_id}.txt
    │       └── ...
"""
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from werkzeug.datastructures import FileStorage

from config import Config


# Allowed file extensions and their categories
ALLOWED_EXTENSIONS: Dict[str, str] = {
    # Documents
    '.pdf': 'document',
    '.txt': 'document',
    '.md': 'document',
    # Audio
    '.mp3': 'audio',
    # Images
    '.avif': 'image',
    '.bmp': 'image',
    '.gif': 'image',
    '.ico': 'image',
    '.jp2': 'image',
    '.png': 'image',
    '.webp': 'image',
    '.tif': 'image',
    '.tiff': 'image',
    '.heic': 'image',
    '.heif': 'image',
    '.jpeg': 'image',
    '.jpg': 'image',
    '.jpe': 'image',
    # Data
    '.csv': 'data',
}

# MIME type mappings
MIME_TYPES: Dict[str, str] = {
    '.pdf': 'application/pdf',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.mp3': 'audio/mpeg',
    '.avif': 'image/avif',
    '.bmp': 'image/bmp',
    '.gif': 'image/gif',
    '.ico': 'image/x-icon',
    '.jp2': 'image/jp2',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.heic': 'image/heic',
    '.heif': 'image/heif',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.jpe': 'image/jpeg',
    '.csv': 'text/csv',
}


class SourceService:
    """
    Service class for managing project sources.

    Educational Note: Sources are raw files uploaded by users. This service
    handles storage and metadata management. Processing (text extraction,
    embedding generation) is handled by separate services.
    """

    def __init__(self):
        """Initialize the source service with the projects directory."""
        self.projects_dir = Config.PROJECTS_DIR

    def _get_sources_dir(self, project_id: str) -> Path:
        """Get the sources directory for a project."""
        return self.projects_dir / project_id / "sources"

    def _get_raw_dir(self, project_id: str) -> Path:
        """Get the raw files directory for a project."""
        return self._get_sources_dir(project_id) / "raw"

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

        sources_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)

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

    def _is_allowed_file(self, filename: str) -> bool:
        """
        Check if a file extension is allowed.

        Educational Note: We validate file extensions for security
        and to ensure we can process the file type.
        """
        ext = Path(filename).suffix.lower()
        return ext in ALLOWED_EXTENSIONS

    def _get_file_info(self, filename: str) -> Tuple[str, str, str]:
        """
        Get file extension, category, and MIME type.

        Returns:
            Tuple of (extension, category, mime_type)
        """
        ext = Path(filename).suffix.lower()
        category = ALLOWED_EXTENSIONS.get(ext, 'unknown')
        mime_type = MIME_TYPES.get(ext, 'application/octet-stream')
        return ext, category, mime_type

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
        if not self._is_allowed_file(original_filename):
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS.keys()))
            raise ValueError(f"File type not allowed. Allowed types: {allowed}")

        # Get file info
        ext, category, mime_type = self._get_file_info(original_filename)

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
            "status": "uploaded",  # uploaded -> processing -> ready | error
            "processing_info": None,  # Will hold processing details later
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Uploaded source: {source_metadata['name']} ({source_id})")

        return source_metadata

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
        processing_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a source's metadata.

        Args:
            project_id: The project UUID
            source_id: The source UUID
            name: New display name (optional)
            description: New description (optional)
            status: New status (optional)
            processing_info: Processing details (optional)

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
                if processing_info is not None:
                    source["processing_info"] = processing_info

                source["updated_at"] = datetime.now().isoformat()
                index["sources"][i] = source

                self._save_index(project_id, index)
                print(f"Updated source: {source_id}")

                return source

        return None

    def delete_source(self, project_id: str, source_id: str) -> bool:
        """
        Delete a source and its raw file.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            True if deleted, False if not found
        """
        source = self.get_source(project_id, source_id)
        if not source:
            return False

        # Delete the raw file
        file_path = self._get_raw_dir(project_id) / source["stored_filename"]
        if file_path.exists():
            file_path.unlink()

        # Remove from index
        index = self._load_index(project_id)
        index["sources"] = [s for s in index["sources"] if s["id"] != source_id]
        self._save_index(project_id, index)

        print(f"Deleted source: {source_id}")

        return True

    def get_allowed_extensions(self) -> Dict[str, str]:
        """
        Get the allowed file extensions and their categories.

        Returns:
            Dictionary mapping extensions to categories
        """
        return ALLOWED_EXTENSIONS.copy()

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
