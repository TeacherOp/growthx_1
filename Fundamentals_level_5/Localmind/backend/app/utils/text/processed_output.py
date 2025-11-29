"""
Processed Output - Build and save standardized processed text output.

Educational Note: All source types (PDF, DOCX, images, audio, links, YouTube)
are converted to a standardized text format with page markers. This enables:
1. Consistent chunking for embeddings
2. Page-based citations in chat responses
3. Unified storage format in the processed/ folder

Output Format:
    # Extracted from PDF document: filename.pdf
    # Type: PDF
    # Total pages: 5
    # Processed at: 2024-01-15T10:30:00
    # model_used: claude-sonnet-4-5-20250929
    # character_count: 15000
    # token_count: 3750
    # ---

    === PDF PAGE 1 of 5 ===

    [Page 1 content here]

    === PDF PAGE 2 of 5 ===

    [Page 2 content here]
    ...

Header Rules:
- All metadata keys are ALWAYS present (value can be empty)
- Each source type has specific metadata keys
- token_count shows "200k+" if > 200,000 or API error
- Header ends with "# ---" separator (like chunk files)

The page markers (=== TYPE PAGE N of M ===) are recognized by:
- text/chunking.py for creating embedding chunks
- citation_utils.py for extracting page content for citations
"""
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.utils.path_utils import get_processed_dir
from app.utils.text.page_markers import build_page_marker, SOURCE_TYPE_DISPLAY


# Standard metadata keys per source type (all keys always present)
SOURCE_METADATA_KEYS = {
    "PDF": ["model_used", "character_count", "token_count"],
    "TEXT": ["character_count", "token_count"],
    "DOCX": ["paragraph_count", "table_count", "character_count", "token_count"],
    "PPTX": ["model_used", "slides_processed", "character_count", "token_count"],
    "IMAGE": ["model_used", "content_type", "character_count", "token_count"],
    "AUDIO": ["model_used", "language", "duration", "diarization_enabled", "character_count", "token_count"],
    "LINK": ["url", "title", "content_type", "character_count", "token_count"],
    "YOUTUBE": ["url", "video_id", "language", "is_auto_generated", "duration", "segment_count", "character_count", "token_count"],
}


def _format_token_count(token_count: Any) -> str:
    """
    Format token count for header display.

    Educational Note: Claude API has token limits. If a source is very large
    (>200k tokens) or the API returns an error, we display "200k+" instead
    of the exact count to indicate it's a large file.

    Args:
        token_count: Token count value (int, str, or None)

    Returns:
        Formatted string: exact count or "200k+"
    """
    if token_count is None:
        return "200k+"

    try:
        count = int(token_count)
        if count > 200000:
            return "200k+"
        return str(count)
    except (ValueError, TypeError):
        # If it's already "200k+" or any error
        return "200k+"


def build_processed_output(
    pages: List[str],
    source_type: str,
    source_name: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build standardized processed text output with page markers.

    Educational Note: This function creates a consistent format for all
    processed sources. The output includes:
    1. Header with source info and ALL metadata keys for this type
    2. Header ends with "# ---" separator
    3. Page markers that chunking/citation utils recognize
    4. Clean page content

    Args:
        pages: List of page content strings (already extracted/split)
        source_type: Type of source (PDF, TEXT, DOCX, PPTX, IMAGE, AUDIO, LINK, YOUTUBE)
        source_name: Display name of the source
        metadata: Metadata dict - all keys for this source type will be included

    Returns:
        Formatted text string ready to save to processed/ folder

    Example:
        pages = ["Page 1 content", "Page 2 content"]
        metadata = {"model_used": "claude-sonnet", "character_count": 1500, "token_count": 375}
        output = build_processed_output(pages, "PDF", "report.pdf", metadata)
    """
    if not pages:
        return ""

    source_type = source_type.upper()
    total_pages = len(pages)
    metadata = metadata or {}

    # Build header using shared display names
    type_display = SOURCE_TYPE_DISPLAY.get(source_type, source_type.lower())
    content = f"# Extracted from {type_display}: {source_name}\n"
    content += f"# Type: {source_type}\n"
    content += f"# Total pages: {total_pages}\n"
    content += f"# Processed at: {datetime.now().isoformat()}\n"

    # Add ALL metadata keys for this source type (value can be empty)
    metadata_keys = SOURCE_METADATA_KEYS.get(source_type, ["character_count", "token_count"])
    for key in metadata_keys:
        value = metadata.get(key, "")
        # Special handling for token_count
        if key == "token_count":
            value = _format_token_count(value)
        # Convert None to empty string
        if value is None:
            value = ""
        content += f"# {key}: {value}\n"

    # End header with separator (like chunk files)
    content += "# ---\n\n"

    # Add each page with marker (using shared marker format)
    for i, page_text in enumerate(pages, start=1):
        marker = build_page_marker(source_type, i, total_pages)
        content += f"{marker}\n\n"
        content += page_text.strip()
        content += "\n\n"

    return content


def save_processed_text(
    project_id: str,
    source_id: str,
    content: str
) -> Path:
    """
    Save processed text content to the processed/ folder.

    Educational Note: All processed sources are saved as .txt files
    in data/projects/{project_id}/sources/processed/{source_id}.txt

    This centralizes the file writing logic so processors don't need
    to handle paths themselves.

    Args:
        project_id: The project UUID
        source_id: The source UUID
        content: The processed text content to save

    Returns:
        Path to the saved file
    """
    processed_dir = get_processed_dir(project_id)
    processed_path = processed_dir / f"{source_id}.txt"

    with open(processed_path, "w", encoding="utf-8") as f:
        f.write(content)

    return processed_path


def build_and_save_processed_output(
    project_id: str,
    source_id: str,
    pages: List[str],
    source_type: str,
    source_name: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build processed output and save to file in one step.

    Educational Note: This is a convenience function that combines
    build_processed_output() and save_processed_text(). Most processors
    can use this single function to handle their output.

    Args:
        project_id: The project UUID
        source_id: The source UUID
        pages: List of page content strings
        source_type: Type of source (PDF, TEXT, etc.)
        source_name: Display name of the source
        metadata: Optional additional metadata

    Returns:
        Dict with:
        - content: The full processed text
        - path: Path to the saved file
        - total_pages: Number of pages
        - character_count: Total character count
    """
    content = build_processed_output(
        pages=pages,
        source_type=source_type,
        source_name=source_name,
        metadata=metadata
    )

    path = save_processed_text(project_id, source_id, content)

    return {
        "content": content,
        "path": path,
        "total_pages": len(pages),
        "character_count": len(content)
    }
