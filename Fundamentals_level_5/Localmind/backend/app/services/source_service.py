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
    │   └── processed/            # Extracted/processed text content
    │       ├── {source_id}.txt   # Extracted text from PDFs, images, etc.
    │       └── ...

Processing Flow:
    1. User uploads file → saved to raw/
    2. Auto-processing triggered based on file type:
       - PDF → text extraction via Claude (pdf_service)
       - TXT/MD → already text, copy to processed/
       - Images → OCR via Claude (future)
       - URLs → content fetching (future)
    3. Status updated: uploaded → processing → ready | error
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from werkzeug.datastructures import FileStorage

from config import Config
from app.services.task_service import task_service


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
    # Links (stored as JSON with URL metadata)
    '.link': 'link',
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
    '.link': 'application/json',
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

    def _process_embeddings_for_source(
        self,
        project_id: str,
        source_id: str,
        source_name: str
    ) -> Dict[str, Any]:
        """
        Process embeddings for a source after text extraction.

        Educational Note: This method is called after successful text extraction.
        It reads the processed text, checks if embeddings are needed (based on
        token count), and if so:
        1. Updates status to "embedding" (so frontend shows embedding in progress)
        2. Creates chunks, embeddings, and upserts to Pinecone
        3. Returns embedding_info (caller will then set status to "ready")

        Status flow:
        - If embeddings needed: processing → embedding → ready
        - If not needed: processing → ready (embedding status skipped)

        Args:
            project_id: The project UUID
            source_id: The source UUID
            source_name: Display name of the source

        Returns:
            Dict with embedding_info to store in source metadata
        """
        # Read the processed text
        processed_path = self._get_processed_dir(project_id) / f"{source_id}.txt"

        if not processed_path.exists():
            return {
                "is_embedded": False,
                "embedded_at": None,
                "token_count": 0,
                "chunk_count": 0,
                "reason": "Processed text file not found"
            }

        try:
            with open(processed_path, "r", encoding="utf-8") as f:
                processed_text = f.read()

            # Import here to avoid circular imports
            from app.services.embedding_check_service import embedding_check_service
            from app.services.embedding_workflow_service import embedding_workflow_service

            # First check if embeddings are needed
            needs_embedding, token_count, reason = embedding_check_service.needs_embedding(
                text=processed_text
            )

            if not needs_embedding:
                # No embedding needed - return immediately
                # Status will go directly to "ready"
                return {
                    "is_embedded": False,
                    "embedded_at": None,
                    "token_count": token_count,
                    "chunk_count": 0,
                    "reason": reason
                }

            # Embeddings needed - update status to "embedding" before starting
            # Educational Note: This lets the frontend show "Embedding..." status
            self.update_source(project_id, source_id, status="embedding")
            print(f"Starting embedding for {source_name} (token count: {token_count})")

            # Process embeddings using the workflow service
            chunks_dir = self._get_chunks_dir(project_id)
            embedding_info = embedding_workflow_service.process_embeddings(
                project_id=project_id,
                source_id=source_id,
                source_name=source_name,
                processed_text=processed_text,
                chunks_dir=chunks_dir
            )

            return embedding_info

        except Exception as e:
            print(f"Error processing embeddings for {source_id}: {e}")
            return {
                "is_embedded": False,
                "embedded_at": None,
                "token_count": 0,
                "chunk_count": 0,
                "reason": f"Embedding error: {str(e)}"
            }

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
            "active": False,  # Whether source is included in chat context (set to True when ready)
            "processing_info": None,  # Will hold processing details later
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Uploaded source: {source_metadata['name']} ({source_id})")

        # Submit processing as a background task
        # Educational Note: Using ThreadPoolExecutor allows the upload to return
        # immediately while processing happens in the background. The user can
        # continue chatting or uploading more files while PDFs are being processed.
        task_service.submit_task(
            "source_processing",  # task_type
            source_id,            # target_id
            self.process_source,  # callable_func
            project_id,           # *args passed to callable
            source_id
        )

        return source_metadata

    def process_source(self, project_id: str, source_id: str) -> Dict[str, Any]:
        """
        Process a source file to extract text content.

        Educational Note: This method handles different file types:
        - PDF: Uses Claude API (via pdf_service) to extract text
        - TXT/MD: Already text, just copy to processed folder
        - Images: Future - OCR via Claude
        - URLs: Future - Content fetching

        The extracted text is saved to the processed/ folder and the
        source status is updated accordingly.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Updated source metadata with processing info
        """
        source = self.get_source(project_id, source_id)
        if not source:
            return {"success": False, "error": "Source not found"}

        file_ext = source.get("file_extension", "").lower()
        raw_file_path = self._get_raw_dir(project_id) / source["stored_filename"]

        # Update status to processing
        self.update_source(project_id, source_id, status="processing")

        try:
            if file_ext == ".pdf":
                # Use pdf_service to extract text from PDF
                # Educational Note: pdf_service processes PDFs in PARALLEL using ThreadPoolExecutor
                # Result is either "ready" (all pages succeeded) or "error" (any page failed)
                # No partial status - we either succeed completely or fail completely
                from app.services.pdf_service import pdf_service

                result = pdf_service.extract_text_from_pdf(
                    project_id=project_id,
                    source_id=source_id,
                    pdf_path=raw_file_path
                )

                if result.get("success"):
                    # All pages extracted successfully
                    processing_info = {
                        "processor": "pdf_service_parallel",
                        "model_used": result.get("model_used"),
                        "total_pages": result.get("total_pages"),
                        "pages_processed": result.get("pages_processed"),
                        "character_count": result.get("character_count"),
                        "token_usage": result.get("token_usage"),
                        "extracted_at": result.get("extracted_at"),
                        "parallel_workers": result.get("parallel_workers")
                    }

                    # Process embeddings if needed
                    # Educational Note: After text extraction, we check if the source
                    # needs embeddings (based on token count). If so, we create chunks,
                    # generate embeddings, and upsert to Pinecone.
                    embedding_info = self._process_embeddings_for_source(
                        project_id=project_id,
                        source_id=source_id,
                        source_name=source.get("name", "")
                    )

                    self.update_source(
                        project_id,
                        source_id,
                        status="ready",
                        processing_info=processing_info,
                        embedding_info=embedding_info
                    )
                    return {"success": True, "status": "ready"}
                elif result.get("status") == "cancelled":
                    # Processing was cancelled by user
                    # Educational Note: Cancelled processing sets status back to "uploaded"
                    # so user can retry later. Raw file is preserved.
                    self.update_source(
                        project_id,
                        source_id,
                        status="uploaded",
                        processing_info={
                            "cancelled": True,
                            "cancelled_at": datetime.now().isoformat(),
                            "total_pages": result.get("total_pages")
                        }
                    )
                    return {"success": False, "status": "cancelled", "error": "Processing cancelled"}
                else:
                    # Extraction failed - no partial content kept
                    # Educational Note: On failure, pdf_service already cleaned up
                    # any partial output files. We update status to "error" so user
                    # can see it failed and retry.
                    self.update_source(
                        project_id,
                        source_id,
                        status="error",
                        processing_info={
                            "error": result.get("error"),
                            "failed_pages": result.get("failed_pages"),
                            "total_pages": result.get("total_pages")
                        }
                    )
                    return {"success": False, "error": result.get("error")}

            elif file_ext in [".txt", ".md"]:
                # Text files are already processed - copy to processed folder
                processed_dir = self._get_processed_dir(project_id)
                processed_path = processed_dir / f"{source_id}.txt"

                # Read and copy content
                with open(raw_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                with open(processed_path, "w", encoding="utf-8") as f:
                    f.write(content)

                processing_info = {
                    "processor": "direct_copy",
                    "character_count": len(content),
                    "extracted_at": datetime.now().isoformat()
                }

                # Process embeddings if needed
                embedding_info = self._process_embeddings_for_source(
                    project_id=project_id,
                    source_id=source_id,
                    source_name=source.get("name", "")
                )

                self.update_source(
                    project_id,
                    source_id,
                    status="ready",
                    active=True,  # Auto-activate when ready
                    processing_info=processing_info,
                    embedding_info=embedding_info
                )
                return {"success": True, "status": "ready"}

            else:
                # Unsupported file type for processing (images, audio, etc.)
                # Mark as uploaded but not processed
                self.update_source(
                    project_id,
                    source_id,
                    status="uploaded",
                    processing_info={"note": "Processing not yet supported for this file type"}
                )
                return {"success": True, "status": "uploaded", "note": "No processing needed"}

        except Exception as e:
            print(f"Error processing source {source_id}: {e}")
            self.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": str(e)}
            )
            return {"success": False, "error": str(e)}

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
        embedding_info: Optional[Dict[str, Any]] = None
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
            embedding_info: Embedding details (optional) - contains:
                - is_embedded: bool
                - embedded_at: timestamp
                - token_count: int
                - chunk_count: int
                - reason: str

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
                    # Educational Note: We no longer use "partial" status - it's either
                    # "ready" (all pages extracted) or "error" (any failure)
                    if status == "ready":
                        source["active"] = True
                if active is not None:
                    source["active"] = active
                if processing_info is not None:
                    source["processing_info"] = processing_info
                if embedding_info is not None:
                    source["embedding_info"] = embedding_info

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
        # Educational Note: This handles Pinecone deletion and chunk file cleanup
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

    def get_allowed_extensions(self) -> Dict[str, str]:
        """
        Get the allowed file extensions and their categories.

        Returns:
            Dictionary mapping extensions to categories
        """
        return ALLOWED_EXTENSIONS.copy()

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
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
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
            "fetched": False,  # Will be set to True after content is fetched
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
            "original_filename": url,  # Store URL as original filename
            "description": description,
            "category": "link",
            "mime_type": "application/json",
            "file_extension": ".link",
            "file_size": file_size,
            "stored_filename": stored_filename,
            "status": "uploaded",
            "active": False,  # Set to True when processed
            "processing_info": {"link_type": link_type},
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Added URL source: {url} ({source_id})")

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
            "active": False,  # Set to True when processed
            "processing_info": {"source_type": "pasted_text"},
            "created_at": timestamp,
            "updated_at": timestamp
        }

        # Update index
        index = self._load_index(project_id)
        index["sources"].append(source_metadata)
        self._save_index(project_id, index)

        print(f"Added text source: {name} ({source_id})")

        # Submit processing as background task (copies to processed folder)
        task_service.submit_task(
            "source_processing",  # task_type
            source_id,            # target_id
            self.process_source,  # callable_func
            project_id,           # *args passed to callable
            source_id
        )

        return source_metadata

    def cancel_processing(self, project_id: str, source_id: str) -> bool:
        """
        Cancel processing for a source.

        Educational Note: This cancels any running tasks for the source and
        cleans up processed data, but keeps the raw file so user can retry.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            True if cancellation was initiated, False otherwise
        """
        source = self.get_source(project_id, source_id)
        if not source:
            return False

        # Only cancel if currently processing
        if source["status"] not in ["uploaded", "processing"]:
            return False

        # Cancel any running tasks for this source
        cancelled_count = task_service.cancel_tasks_for_target(source_id)
        print(f"Cancelled {cancelled_count} tasks for source {source_id}")

        # Delete processed file if it exists (keep raw file!)
        processed_path = self._get_processed_dir(project_id) / f"{source_id}.txt"
        if processed_path.exists():
            processed_path.unlink()
            print(f"Deleted partial processed file: {processed_path}")

        # Update source status to uploaded (ready to retry)
        self.update_source(
            project_id,
            source_id,
            status="uploaded",
            processing_info={"cancelled": True, "cancelled_at": datetime.now().isoformat()}
        )

        return True

    def retry_processing(self, project_id: str, source_id: str) -> Dict[str, Any]:
        """
        Retry processing for a source that failed or was cancelled.

        Educational Note: This submits a new processing task for the source.
        Only works for sources that have a raw file but are not currently processing.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Dict with success status and message
        """
        source = self.get_source(project_id, source_id)
        if not source:
            return {"success": False, "error": "Source not found"}

        # Can only retry if status is uploaded or error (not processing)
        if source["status"] == "processing":
            return {"success": False, "error": "Source is already processing"}

        if source["status"] == "ready":
            return {"success": False, "error": "Source is already processed"}

        # Verify raw file exists
        raw_file_path = self._get_raw_dir(project_id) / source["stored_filename"]
        if not raw_file_path.exists():
            return {"success": False, "error": "Raw file not found"}

        # Delete any existing processed file
        processed_path = self._get_processed_dir(project_id) / f"{source_id}.txt"
        if processed_path.exists():
            processed_path.unlink()

        # Update status to uploaded (processing will be done by background task)
        self.update_source(
            project_id,
            source_id,
            status="uploaded",
            processing_info={"retry": True, "retry_at": datetime.now().isoformat()}
        )

        # Submit new processing task
        task_service.submit_task(
            "source_processing",
            source_id,
            self.process_source,
            project_id,
            source_id
        )

        return {"success": True, "message": "Processing restarted"}

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
