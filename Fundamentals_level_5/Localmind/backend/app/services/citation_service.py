"""
Citation Service - Extract page content from processed source files.

Educational Note: This service enables the citation feature by extracting
specific page content from processed source files. When Claude cites a source
with [[cite:SOURCE_ID:PAGE]], the frontend can fetch the actual page content
to display in a tooltip.

Page Marker Formats (from chunking_service.py):
    === PDF PAGE 1 of 10 ===     (from PDF extraction)
    === TEXT PAGE 1 of 5 ===     (from text file processing)
    === DOCX PAGE 1 of 5 ===     (from Word document processing)
    === PPTX PAGE 1 of 10 ===    (from PowerPoint presentation processing)
    === AUDIO PAGE 1 of 5 ===    (from audio transcription)
    === LINK PAGE 1 of 5 ===     (from URL/link extraction)
    === YOUTUBE PAGE 1 of 5 ===  (from YouTube transcripts)
    === IMAGE PAGE 1 of 1 ===    (from image extraction)
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from config import Config


class CitationService:
    """
    Service for extracting page content from processed source files.

    Educational Note: Processed files contain extracted text with page markers.
    This service parses those markers to extract content for specific pages,
    enabling the citation tooltip feature in the frontend.
    """

    def __init__(self):
        """Initialize the citation service with the projects directory."""
        self.projects_dir = Config.PROJECTS_DIR

        # Regex pattern to match any page marker format
        # Matches: === TYPE PAGE X of Y === or === TYPE PAGE X of Y (continues from previous) ===
        # Where TYPE can be: PDF, TEXT, DOCX, PPTX, AUDIO, LINK, YOUTUBE, IMAGE
        # The optional (?:\s+\([^)]+\))? handles markers like "(continues from previous)"
        self.page_marker_pattern = re.compile(
            r'^===\s*(PDF|TEXT|DOCX|PPTX|AUDIO|LINK|YOUTUBE|IMAGE)\s+PAGE\s+(\d+)\s+of\s+(\d+)(?:\s+\([^)]+\))?\s*===\s*$',
            re.MULTILINE
        )

    def _get_processed_file_path(self, project_id: str, source_id: str) -> Path:
        """Get the path to a processed source file."""
        return self.projects_dir / project_id / "sources" / "processed" / f"{source_id}.txt"

    def get_page_content(
        self,
        project_id: str,
        source_id: str,
        page_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content for a specific page from a processed source file.

        Educational Note: This method parses the processed file, finds the
        page marker for the requested page, and extracts the content between
        that marker and the next one (or end of file).

        Args:
            project_id: The project UUID
            source_id: The source UUID
            page_number: The page number to extract (1-indexed)

        Returns:
            Dictionary with page content and metadata, or None if not found:
            {
                "content": "The actual page text...",
                "page_number": 1,
                "total_pages": 10,
                "source_type": "PDF"
            }
        """
        processed_path = self._get_processed_file_path(project_id, source_id)

        if not processed_path.exists():
            return None

        try:
            with open(processed_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading processed file: {e}")
            return None

        # Find all page markers in the file
        matches = list(self.page_marker_pattern.finditer(content))

        if not matches:
            # No page markers found - might be an image or single-page source
            # Return entire content as page 1
            if page_number == 1:
                # Remove header comments if present
                lines = content.split('\n')
                content_start = 0
                for i, line in enumerate(lines):
                    if not line.startswith('#') and line.strip():
                        content_start = i
                        break

                return {
                    "content": '\n'.join(lines[content_start:]).strip(),
                    "page_number": 1,
                    "total_pages": 1,
                    "source_type": "UNKNOWN"
                }
            return None

        # Find the requested page
        target_match = None
        next_match = None

        for i, match in enumerate(matches):
            current_page = int(match.group(2))
            if current_page == page_number:
                target_match = match
                # Get next match if exists
                if i + 1 < len(matches):
                    next_match = matches[i + 1]
                break

        if not target_match:
            return None

        # Extract content between this marker and the next (or end of file)
        start_pos = target_match.end()
        end_pos = next_match.start() if next_match else len(content)

        page_content = content[start_pos:end_pos].strip()

        return {
            "content": page_content,
            "page_number": page_number,
            "total_pages": int(target_match.group(3)),
            "source_type": target_match.group(1)
        }

    def get_all_pages(
        self,
        project_id: str,
        source_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract all pages from a processed source file.

        Educational Note: This is useful for getting an overview of the source
        or for batch operations. Returns a list of page content dictionaries.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            List of page dictionaries, each with content and metadata
        """
        processed_path = self._get_processed_file_path(project_id, source_id)

        if not processed_path.exists():
            return []

        try:
            with open(processed_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading processed file: {e}")
            return []

        # Find all page markers
        matches = list(self.page_marker_pattern.finditer(content))

        if not matches:
            # No markers - return entire content as single page
            lines = content.split('\n')
            content_start = 0
            for i, line in enumerate(lines):
                if not line.startswith('#') and line.strip():
                    content_start = i
                    break

            return [{
                "content": '\n'.join(lines[content_start:]).strip(),
                "page_number": 1,
                "total_pages": 1,
                "source_type": "UNKNOWN"
            }]

        pages = []
        for i, match in enumerate(matches):
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)

            page_content = content[start_pos:end_pos].strip()

            pages.append({
                "content": page_content,
                "page_number": int(match.group(2)),
                "total_pages": int(match.group(3)),
                "source_type": match.group(1)
            })

        return pages

    def get_page_count(self, project_id: str, source_id: str) -> int:
        """
        Get the total number of pages in a processed source file.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Total page count, or 0 if file not found
        """
        processed_path = self._get_processed_file_path(project_id, source_id)

        if not processed_path.exists():
            return 0

        try:
            with open(processed_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading processed file: {e}")
            return 0

        # Find any page marker to get total count
        match = self.page_marker_pattern.search(content)

        if match:
            return int(match.group(3))

        # No markers - assume single page
        return 1


# Singleton instance
citation_service = CitationService()
