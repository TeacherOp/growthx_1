"""
Source Context Service - Builds dynamic source context for chat system prompts.

Educational Note: This service creates a formatted list of available sources
that gets appended to the system prompt. This allows the AI to know:
- Which sources are available to search
- Source IDs (needed for the search_sources tool)
- Source types and names (to pick the right source for a question)
- Whether a source is embedded (affects search behavior)
- Source summaries (to understand content and pick the right source)

The context is rebuilt on every message to reflect the current state
of sources (active/inactive toggles, new uploads, deletions).
"""
from typing import Dict, Any, List

from app.services.source_service import source_service


class SourceContextService:
    """
    Service for building source context for chat prompts.

    Educational Note: This service is called by main_chat_service
    before each API call to build up-to-date source context.
    """

    def get_active_sources(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get list of active and ready sources for a project.

        Educational Note: A source must be both:
        - status: "ready" (processing complete)
        - active: True (user hasn't disabled it)

        Args:
            project_id: The project UUID

        Returns:
            List of source metadata dicts for active/ready sources
        """
        all_sources = source_service.list_sources(project_id)

        active_sources = [
            source for source in all_sources
            if source.get("status") == "ready" and source.get("active", False)
        ]

        return active_sources

    def build_source_context(self, project_id: str) -> str:
        """
        Build formatted source context for the system prompt.

        Educational Note: This creates a structured text block that tells
        the AI what sources are available and how to reference them.
        The format is designed to be clear and parseable by the model.

        Args:
            project_id: The project UUID

        Returns:
            Formatted string to append to system prompt, or empty string if no sources
        """
        active_sources = self.get_active_sources(project_id)

        if not active_sources:
            return ""

        # Build the context block
        lines = [
            "",
            "## Available Sources",
            "",
            "You have access to the following sources. Use the search_sources tool to retrieve information when answering questions.",
            "",
        ]

        for source in active_sources:
            source_id = source.get("id", "")
            name = source.get("name", "Unknown")
            category = source.get("category", "unknown")
            file_ext = source.get("file_extension", "")

            # Check if embedded
            embedding_info = source.get("embedding_info", {})
            is_embedded = embedding_info.get("is_embedded", False)
            embedded_label = "Yes" if is_embedded else "No"

            # Get summary if available
            summary_info = source.get("summary_info", {})
            summary_text = summary_info.get("summary", "")

            # Format source type from category and extension
            source_type = self._format_source_type(category, file_ext)

            lines.append(f"- **{name}**")
            lines.append(f"  - ID: `{source_id}`")
            lines.append(f"  - Type: {source_type}")
            lines.append(f"  - Embedded: {embedded_label}")
            if summary_text:
                lines.append(f"  - Summary: {summary_text}")
            lines.append("")

        lines.append("When the user asks about content from these sources, use the search_sources tool with the appropriate source_id.")
        lines.append("")

        return "\n".join(lines)

    def _format_source_type(self, category: str, file_ext: str) -> str:
        """
        Format a human-readable source type from category and extension.

        Args:
            category: Source category (document, image, audio, link, etc.)
            file_ext: File extension (.pdf, .txt, .mp3, etc.)

        Returns:
            Human-readable type string
        """
        # Map common extensions to readable names
        ext_map = {
            ".pdf": "PDF Document",
            ".docx": "Word Document",
            ".doc": "Word Document",
            ".txt": "Text File",
            ".pptx": "PowerPoint",
            ".ppt": "PowerPoint",
            ".mp3": "Audio (MP3)",
            ".wav": "Audio (WAV)",
            ".m4a": "Audio (M4A)",
            ".png": "Image (PNG)",
            ".jpg": "Image (JPEG)",
            ".jpeg": "Image (JPEG)",
            ".webp": "Image (WebP)",
            ".link": "Web Link",
        }

        if file_ext in ext_map:
            return ext_map[file_ext]

        # Fallback to category
        category_map = {
            "document": "Document",
            "image": "Image",
            "audio": "Audio",
            "link": "Web Content",
            "video": "Video",
        }

        return category_map.get(category, category.title())


# Singleton instance
source_context_service = SourceContextService()
