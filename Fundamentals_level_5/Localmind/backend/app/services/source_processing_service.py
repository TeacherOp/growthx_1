"""
Source Processing Service - Handles processing orchestration for sources.

Educational Note: This service manages the processing pipeline for sources:
- PDF text extraction (via pdf_service)
- Text file processing (direct copy)
- Embedding generation (via embedding_workflow_service)
- Cancel/retry operations

Processing Flow:
    1. Source uploaded -> status: "uploaded"
    2. Processing starts -> status: "processing"
    3. If embeddings needed -> status: "embedding"
    4. Complete -> status: "ready" | "error"

Separated from source_service.py to maintain single responsibility:
- source_service: CRUD operations, uploads, path/index management
- source_processing_service: Processing orchestration
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class SourceProcessingService:
    """
    Service class for processing source files.

    Educational Note: This service orchestrates the processing pipeline.
    It imports source_service to access CRUD operations and path utilities.
    """

    def process_source(self, project_id: str, source_id: str) -> Dict[str, Any]:
        """
        Process a source file to extract text content.

        Educational Note: This method handles different file types:
        - PDF: Uses Claude API (via pdf_service) to extract text with OCR
        - TXT: Split into pages and save with markers
        - DOCX: Uses python-docx to extract text, preserves structure as markdown
        - Images: Uses Claude vision (via image_service) to extract content
        - PPTX: Converts to PDF via LibreOffice, analyzes slides with Claude vision
        - Audio: Uses ElevenLabs Scribe v1 for transcription
        - URLs: Future - Content fetching

        The extracted text is saved to the processed/ folder and the
        source status is updated accordingly.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Dict with success status and processing info
        """
        # Import here to avoid circular imports
        from app.services.source_service import source_service

        source = source_service.get_source(project_id, source_id)
        if not source:
            return {"success": False, "error": "Source not found"}

        file_ext = source.get("file_extension", "").lower()
        raw_file_path = source_service._get_raw_dir(project_id) / source["stored_filename"]

        # Update status to processing
        source_service.update_source(project_id, source_id, status="processing")

        try:
            if file_ext == ".pdf":
                return self._process_pdf(
                    project_id, source_id, source, raw_file_path, source_service
                )

            elif file_ext in [".txt"]:
                return self._process_text_file(
                    project_id, source_id, source, raw_file_path, source_service
                )

            elif file_ext == ".docx":
                return self._process_docx(
                    project_id, source_id, source, raw_file_path, source_service
                )

            elif file_ext in [".jpeg", ".jpg", ".png", ".gif", ".webp"]:
                return self._process_image(
                    project_id, source_id, source, raw_file_path, source_service
                )

            elif file_ext == ".pptx":
                return self._process_pptx(
                    project_id, source_id, source, raw_file_path, source_service
                )

            elif file_ext in [".mp3", ".wav", ".m4a", ".aac", ".flac"]:
                return self._process_audio(
                    project_id, source_id, source, raw_file_path, source_service
                )

            elif file_ext == ".link":
                return self._process_link(
                    project_id, source_id, source, raw_file_path, source_service
                )

            else:
                # Unsupported file type for processing
                source_service.update_source(
                    project_id,
                    source_id,
                    status="uploaded",
                    processing_info={"note": "Processing not yet supported for this file type"}
                )
                return {"success": True, "status": "uploaded", "note": "No processing needed"}

        except Exception as e:
            print(f"Error processing source {source_id}: {e}")
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": str(e)}
            )
            return {"success": False, "error": str(e)}

    def _process_pdf(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process a PDF file - extract text and optionally create embeddings.

        Educational Note: pdf_service processes PDFs in PARALLEL using ThreadPoolExecutor.
        Result is either "ready" (all pages succeeded) or "error" (any page failed).
        No partial status - we either succeed completely or fail completely.
        """
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
            embedding_info = self._process_embeddings_for_source(
                project_id=project_id,
                source_id=source_id,
                source_name=source.get("name", ""),
                source_service=source_service
            )

            # Generate summary after embeddings
            source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
            summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

            source_service.update_source(
                project_id,
                source_id,
                status="ready",
                processing_info=processing_info,
                embedding_info=embedding_info,
                summary_info=summary_info if summary_info else None
            )
            return {"success": True, "status": "ready"}

        elif result.get("status") == "cancelled":
            # Processing was cancelled by user
            source_service.update_source(
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
            source_service.update_source(
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

    def _process_text_file(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process a text file - split into pages and save to processed folder.

        Educational Note: Text files need to be split into logical "pages" for
        effective RAG chunking. We use text_utils to split at ~3500 characters,
        finding the nearest paragraph end or newline within 500 chars of target.

        This creates page markers like: === TEXT PAGE 1 of 5 ===
        which the chunking service recognizes for creating embeddings.
        """
        from app.utils.text_utils import split_text_into_pages, format_text_with_page_markers

        processed_dir = source_service._get_processed_dir(project_id)
        processed_path = processed_dir / f"{source_id}.txt"

        # Read raw content
        with open(raw_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into logical pages and format with markers
        pages = split_text_into_pages(content)
        source_name = source.get("name", "unknown")
        processed_content = format_text_with_page_markers(pages, source_name)

        # Save processed content
        with open(processed_path, "w", encoding="utf-8") as f:
            f.write(processed_content)

        processing_info = {
            "processor": "text_page_splitter",
            "character_count": len(content),
            "total_pages": len(pages),
            "extracted_at": datetime.now().isoformat()
        }

        # Process embeddings if needed
        embedding_info = self._process_embeddings_for_source(
            project_id=project_id,
            source_id=source_id,
            source_name=source_name,
            source_service=source_service
        )

        # Generate summary after embeddings
        source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
        summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

        source_service.update_source(
            project_id,
            source_id,
            status="ready",
            active=True,  # Auto-activate when ready
            processing_info=processing_info,
            embedding_info=embedding_info,
            summary_info=summary_info if summary_info else None
        )
        return {"success": True, "status": "ready"}

    def _process_docx(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process a DOCX file - extract text and save to processed folder.

        Educational Note: DOCX files are processed using python-docx library.
        The extracted text preserves document structure (headings, lists, tables)
        in a markdown-like format. We then split into pages using the same
        character-based logic as text files.

        This creates page markers like: === DOCX PAGE 1 of 5 ===
        which the chunking service recognizes for creating embeddings.
        """
        from app.services.docx_service import docx_service
        from app.utils.text_utils import split_text_into_pages, format_text_with_page_markers

        # Extract text from DOCX
        result = docx_service.extract_text_from_docx(raw_file_path)

        if not result.get("success"):
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": result.get("error")}
            )
            return {"success": False, "error": result.get("error")}

        # Get extracted content
        content = result.get("text", "")
        source_name = source.get("name", "unknown")

        # Split into logical pages and format with markers
        pages = split_text_into_pages(content)
        processed_content = format_text_with_page_markers(pages, source_name, source_type="DOCX")

        # Save processed content
        processed_dir = source_service._get_processed_dir(project_id)
        processed_path = processed_dir / f"{source_id}.txt"
        with open(processed_path, "w", encoding="utf-8") as f:
            f.write(processed_content)

        processing_info = {
            "processor": "docx_service",
            "character_count": len(content),
            "total_pages": len(pages),
            "paragraph_count": result.get("paragraph_count", 0),
            "table_count": result.get("table_count", 0),
            "extracted_at": result.get("extracted_at")
        }

        # Process embeddings if needed
        embedding_info = self._process_embeddings_for_source(
            project_id=project_id,
            source_id=source_id,
            source_name=source_name,
            source_service=source_service
        )

        # Generate summary after embeddings
        source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
        summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

        source_service.update_source(
            project_id,
            source_id,
            status="ready",
            active=True,  # Auto-activate when ready
            processing_info=processing_info,
            embedding_info=embedding_info,
            summary_info=summary_info if summary_info else None
        )
        return {"success": True, "status": "ready"}

    def _process_image(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process an image file - extract content using Claude vision.

        Educational Note: image_service uses Claude's vision capability to
        analyze images and extract structured content including text, visual
        descriptions, data from charts/tables, and summaries.
        """
        from app.services.image_service import image_service

        result = image_service.extract_content_from_image(
            project_id=project_id,
            source_id=source_id,
            image_path=raw_file_path
        )

        if result.get("success"):
            processing_info = {
                "processor": "image_service",
                "model_used": result.get("model_used"),
                "content_type": result.get("content_type"),
                "character_count": result.get("character_count"),
                "token_usage": result.get("token_usage"),
                "extracted_at": result.get("extracted_at")
            }

            # Process embeddings if needed
            embedding_info = self._process_embeddings_for_source(
                project_id=project_id,
                source_id=source_id,
                source_name=source.get("name", ""),
                source_service=source_service
            )

            # Generate summary after embeddings
            source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
            summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

            source_service.update_source(
                project_id,
                source_id,
                status="ready",
                processing_info=processing_info,
                embedding_info=embedding_info,
                summary_info=summary_info if summary_info else None
            )
            return {"success": True, "status": "ready"}

        else:
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": result.get("error")}
            )
            return {"success": False, "error": result.get("error")}

    def _process_pptx(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process a PPTX file - convert to PDF, analyze slides with Claude vision.

        Educational Note: PPTX files are processed in three stages:
        1. Convert PPTX to PDF using LibreOffice headless
        2. Extract PDF pages as base64 (reusing existing infrastructure)
        3. Send to Claude vision with presentation-specific prompts

        This creates page markers like: === PPTX PAGE 1 of 10 ===
        which the chunking service recognizes for creating embeddings.
        """
        from app.services.pptx_service import pptx_service

        # Extract content using PPTX service (handles conversion + vision analysis)
        result = pptx_service.extract_content_from_pptx(
            project_id=project_id,
            source_id=source_id,
            pptx_path=raw_file_path
        )

        if result.get("success"):
            processing_info = {
                "processor": "pptx_service",
                "model_used": result.get("model_used"),
                "total_slides": result.get("total_slides"),
                "slides_processed": result.get("slides_processed"),
                "character_count": result.get("character_count"),
                "token_usage": result.get("token_usage"),
                "extracted_at": result.get("extracted_at")
            }

            # Process embeddings if needed
            embedding_info = self._process_embeddings_for_source(
                project_id=project_id,
                source_id=source_id,
                source_name=source.get("name", ""),
                source_service=source_service
            )

            # Generate summary after embeddings
            source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
            summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

            source_service.update_source(
                project_id,
                source_id,
                status="ready",
                processing_info=processing_info,
                embedding_info=embedding_info,
                summary_info=summary_info if summary_info else None
            )
            return {"success": True, "status": "ready"}

        else:
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": result.get("error")}
            )
            return {"success": False, "error": result.get("error")}

    def _process_audio(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process an audio file - transcribe using ElevenLabs Speech-to-Text.

        Educational Note: Audio files are transcribed using ElevenLabs' Scribe v1
        model, which provides high-accuracy transcription with optional speaker
        diarization and audio event detection.

        The transcript is split into pages using character-based splitting (6500 chars)
        with markers like: === AUDIO PAGE 1 of 5 ===
        """
        from app.services.audio_service import audio_service

        # Check if ElevenLabs is configured
        if not audio_service.is_configured():
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": "ELEVENLABS_API_KEY not configured. Please add it in App Settings."}
            )
            return {"success": False, "error": "ELEVENLABS_API_KEY not configured"}

        # Transcribe the audio file
        result = audio_service.transcribe_audio(
            project_id=project_id,
            source_id=source_id,
            audio_path=raw_file_path
        )

        if result.get("success"):
            processing_info = {
                "processor": "audio_service",
                "model_used": result.get("model_used"),
                "character_count": result.get("character_count"),
                "detected_language_code": result.get("detected_language_code"),
                "detected_language_name": result.get("detected_language_name"),
                "diarization_enabled": result.get("diarization_enabled"),
                "extracted_at": result.get("extracted_at")
            }

            # Process embeddings if needed
            embedding_info = self._process_embeddings_for_source(
                project_id=project_id,
                source_id=source_id,
                source_name=source.get("name", ""),
                source_service=source_service
            )

            # Generate summary after embeddings
            source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
            summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

            source_service.update_source(
                project_id,
                source_id,
                status="ready",
                processing_info=processing_info,
                embedding_info=embedding_info,
                summary_info=summary_info if summary_info else None
            )
            return {"success": True, "status": "ready"}

        else:
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": result.get("error")}
            )
            return {"success": False, "error": result.get("error")}

    def _process_link(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process a link source - extract content from URL using web agent.

        Educational Note: Link sources are stored as .link files containing JSON
        with the URL and metadata. We use the web_agent_service to fetch and
        extract content from the URL.

        The web agent:
        1. Tries Claude's web_fetch first
        2. Falls back to Tavily search if web_fetch fails
        3. Returns structured content via return_search_result tool

        The extracted content is then split into pages using character-based
        splitting (6500 chars) with markers like: === LINK PAGE 1 of 5 ===
        """
        import json
        from app.services.web_agent_service import web_agent_service
        from app.utils.text_utils import split_text_into_pages

        # Read the .link file to get URL
        with open(raw_file_path, 'r') as f:
            link_data = json.load(f)

        url = link_data.get("url")
        link_type = link_data.get("type", "website")

        if not url:
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": "No URL found in link file"}
            )
            return {"success": False, "error": "No URL found in link file"}

        # Handle YouTube videos separately
        if link_type == "youtube":
            return self._process_youtube(
                project_id, source_id, source, url, link_data, raw_file_path, source_service
            )

        print(f"Processing link source: {url}")

        # Use web agent to extract content (pass project_id and source_id for execution logging)
        result = web_agent_service.extract_from_url(
            url,
            project_id=project_id,
            source_id=source_id
        )

        if not result.get("success"):
            error_msg = result.get("error_message", "Failed to extract content from URL")
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={
                    "error": error_msg,
                    "url": url,
                    "iterations": result.get("iterations"),
                    "usage": result.get("usage")
                }
            )
            return {"success": False, "error": error_msg}

        # Extract content from agent result
        content = result.get("content", "")
        title = result.get("title", url)
        summary = result.get("summary", "")
        content_type = result.get("content_type", "other")
        source_urls = result.get("source_urls", [url])

        if not content:
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": "No content extracted from URL", "url": url}
            )
            return {"success": False, "error": "No content extracted from URL"}

        # Split content into pages
        pages = split_text_into_pages(content)
        total_pages = len(pages)

        # Build processed content with LINK PAGE markers
        processed_content = f"# Extracted from URL: {url}\n"
        processed_content += f"# Title: {title}\n"
        processed_content += f"# Content type: {content_type}\n"
        processed_content += f"# Total pages: {total_pages}\n"
        if summary:
            processed_content += f"# Summary: {summary}\n"
        processed_content += f"# Processed at: {result.get('extracted_at')}\n\n"

        for i, page_text in enumerate(pages, start=1):
            processed_content += f"=== LINK PAGE {i} of {total_pages} ===\n\n"
            processed_content += page_text.strip()
            processed_content += "\n\n"

        # Save processed content
        processed_dir = source_service._get_processed_dir(project_id)
        processed_path = processed_dir / f"{source_id}.txt"
        with open(processed_path, "w", encoding="utf-8") as f:
            f.write(processed_content)

        # Update link file to mark as fetched
        link_data["fetched"] = True
        link_data["fetched_at"] = result.get("extracted_at")
        link_data["title"] = title
        link_data["content_type"] = content_type
        with open(raw_file_path, 'w') as f:
            json.dump(link_data, f, indent=2)

        processing_info = {
            "processor": "web_agent",
            "url": url,
            "title": title,
            "content_type": content_type,
            "character_count": len(content),
            "total_pages": total_pages,
            "source_urls": source_urls,
            "iterations": result.get("iterations"),
            "usage": result.get("usage"),
            "extracted_at": result.get("extracted_at")
        }

        # Process embeddings if needed
        source_name = source.get("name", url)
        embedding_info = self._process_embeddings_for_source(
            project_id=project_id,
            source_id=source_id,
            source_name=source_name,
            source_service=source_service
        )

        # Generate summary after embeddings
        source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
        summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

        source_service.update_source(
            project_id,
            source_id,
            status="ready",
            active=True,  # Auto-activate when ready
            processing_info=processing_info,
            embedding_info=embedding_info,
            summary_info=summary_info if summary_info else None
        )
        return {"success": True, "status": "ready"}

    def _process_youtube(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        url: str,
        link_data: Dict[str, Any],
        raw_file_path: Path,
        source_service
    ) -> Dict[str, Any]:
        """
        Process a YouTube video - fetch transcript using youtube-transcript-api.

        Educational Note: YouTube videos often have captions (manual or auto-generated)
        that we can fetch directly without downloading the video. This is much faster
        than audio transcription and uses existing caption data.

        Transcript priority:
        1. Manual captions (human-created, higher quality)
        2. Auto-generated captions (YouTube's ASR)

        The transcript is then split into pages using character-based splitting
        with markers like: === YOUTUBE PAGE 1 of 5 ===
        """
        import json
        from datetime import datetime
        from app.services.youtube_service import youtube_service
        from app.utils.text_utils import split_text_into_pages

        # Fetch transcript
        result = youtube_service.get_transcript(url, include_timestamps=True)

        if not result.get("success"):
            error_msg = result.get("error_message", "Failed to fetch YouTube transcript")
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={
                    "error": error_msg,
                    "url": url,
                    "video_id": result.get("video_id")
                }
            )
            return {"success": False, "error": error_msg}

        # Extract transcript data
        transcript = result.get("transcript", "")
        video_id = result.get("video_id", "")
        language = result.get("language", "unknown")
        is_auto_generated = result.get("is_auto_generated", False)
        duration_seconds = result.get("duration_seconds", 0)
        segment_count = result.get("segment_count", 0)

        if not transcript:
            source_service.update_source(
                project_id,
                source_id,
                status="error",
                processing_info={"error": "Empty transcript returned", "url": url}
            )
            return {"success": False, "error": "Empty transcript returned"}

        # Format duration for display
        duration_minutes = int(duration_seconds // 60)
        duration_secs = int(duration_seconds % 60)
        duration_str = f"{duration_minutes}:{duration_secs:02d}"

        # Split transcript into pages
        pages = split_text_into_pages(transcript)
        total_pages = len(pages)

        # Build processed content with YOUTUBE PAGE markers
        processed_content = f"# YouTube Video Transcript\n"
        processed_content += f"# URL: {url}\n"
        processed_content += f"# Video ID: {video_id}\n"
        processed_content += f"# Language: {language}\n"
        processed_content += f"# Auto-generated: {is_auto_generated}\n"
        processed_content += f"# Duration: {duration_str}\n"
        processed_content += f"# Segments: {segment_count}\n"
        processed_content += f"# Total pages: {total_pages}\n"
        processed_content += f"# Processed at: {datetime.now().isoformat()}\n\n"

        for i, page_text in enumerate(pages, start=1):
            processed_content += f"=== YOUTUBE PAGE {i} of {total_pages} ===\n\n"
            processed_content += page_text.strip()
            processed_content += "\n\n"

        # Save processed content
        processed_dir = source_service._get_processed_dir(project_id)
        processed_path = processed_dir / f"{source_id}.txt"
        with open(processed_path, "w", encoding="utf-8") as f:
            f.write(processed_content)

        # Update link file with transcript info
        link_data["fetched"] = True
        link_data["fetched_at"] = datetime.now().isoformat()
        link_data["video_id"] = video_id
        link_data["language"] = language
        link_data["is_auto_generated"] = is_auto_generated
        link_data["duration_seconds"] = duration_seconds
        with open(raw_file_path, 'w') as f:
            json.dump(link_data, f, indent=2)

        processing_info = {
            "processor": "youtube_transcript",
            "url": url,
            "video_id": video_id,
            "language": language,
            "is_auto_generated": is_auto_generated,
            "duration": duration_str,
            "duration_seconds": duration_seconds,
            "segment_count": segment_count,
            "character_count": len(transcript),
            "total_pages": total_pages
        }

        # Process embeddings if needed
        source_name = source.get("name", f"YouTube: {video_id}")
        embedding_info = self._process_embeddings_for_source(
            project_id=project_id,
            source_id=source_id,
            source_name=source_name,
            source_service=source_service
        )

        # Generate summary after embeddings
        source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
        summary_info = self._generate_summary_for_source(project_id, source_id, source_metadata)

        source_service.update_source(
            project_id,
            source_id,
            status="ready",
            active=True,
            processing_info=processing_info,
            embedding_info=embedding_info,
            summary_info=summary_info if summary_info else None
        )
        return {"success": True, "status": "ready"}

    def _generate_summary_for_source(
        self,
        project_id: str,
        source_id: str,
        source_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a summary for a processed source.

        Educational Note: This method is called after text extraction and embedding
        to generate a concise summary of the source content. The summary uses:
        - Full content for small sources (not chunked)
        - Sampled chunks for large sources (evenly distributed selection)

        Args:
            project_id: The project UUID
            source_id: The source UUID
            source_metadata: Full source metadata from index

        Returns:
            Dict with summary_info or empty dict if summary generation failed
        """
        try:
            from app.services.summary_service import summary_service

            print(f"Generating summary for source: {source_id}")

            result = summary_service.generate_summary(
                project_id=project_id,
                source_id=source_id,
                source_metadata=source_metadata
            )

            if result:
                print(f"Summary generated for {source_id}: {len(result.get('summary', ''))} chars")
                return result
            else:
                print(f"Summary generation returned None for {source_id}")
                return {}

        except Exception as e:
            print(f"Error generating summary for {source_id}: {e}")
            return {}

    def _process_embeddings_for_source(
        self,
        project_id: str,
        source_id: str,
        source_name: str,
        source_service
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
        - If embeddings needed: processing -> embedding -> ready
        - If not needed: processing -> ready (embedding status skipped)

        Args:
            project_id: The project UUID
            source_id: The source UUID
            source_name: Display name of the source
            source_service: Reference to source_service for updates

        Returns:
            Dict with embedding_info to store in source metadata
        """
        # Read the processed text
        processed_path = source_service._get_processed_dir(project_id) / f"{source_id}.txt"

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
            source_service.update_source(project_id, source_id, status="embedding")
            print(f"Starting embedding for {source_name} (token count: {token_count})")

            # Process embeddings using the workflow service
            chunks_dir = source_service._get_chunks_dir(project_id)
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
        from app.services.source_service import source_service
        from app.services.task_service import task_service

        source = source_service.get_source(project_id, source_id)
        if not source:
            return False

        # Only cancel if currently processing or embedding
        if source["status"] not in ["uploaded", "processing", "embedding"]:
            return False

        # Cancel any running tasks for this source
        cancelled_count = task_service.cancel_tasks_for_target(source_id)
        print(f"Cancelled {cancelled_count} tasks for source {source_id}")

        # Delete processed file if it exists (keep raw file!)
        processed_path = source_service._get_processed_dir(project_id) / f"{source_id}.txt"
        if processed_path.exists():
            processed_path.unlink()
            print(f"Deleted partial processed file: {processed_path}")

        # Update source status to uploaded (ready to retry)
        source_service.update_source(
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
        from app.services.source_service import source_service
        from app.services.task_service import task_service

        source = source_service.get_source(project_id, source_id)
        if not source:
            return {"success": False, "error": "Source not found"}

        # Can only retry if status is uploaded or error (not processing/embedding)
        if source["status"] in ["processing", "embedding"]:
            return {"success": False, "error": "Source is already processing"}

        if source["status"] == "ready":
            return {"success": False, "error": "Source is already processed"}

        # Verify raw file exists
        raw_file_path = source_service._get_raw_dir(project_id) / source["stored_filename"]
        if not raw_file_path.exists():
            return {"success": False, "error": "Raw file not found"}

        # Delete any existing processed file
        processed_path = source_service._get_processed_dir(project_id) / f"{source_id}.txt"
        if processed_path.exists():
            processed_path.unlink()

        # Update status to uploaded (processing will be done by background task)
        source_service.update_source(
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


# Singleton instance
source_processing_service = SourceProcessingService()
