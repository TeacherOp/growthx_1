"""
Page Markers - Shared constants for page marker format.

Educational Note: All processed sources use a standardized page marker format:
    === {TYPE} PAGE {N} of {TOTAL} ===

This module defines:
1. The marker format used when CREATING processed output
2. The regex patterns used when PARSING processed output

Having these in one place ensures consistency between:
- processed_output.py (creates markers)
- chunking.py (parses markers)
- citation_utils.py (extracts page content)
"""
import re
from typing import List


# =============================================================================
# SUPPORTED SOURCE TYPES
# =============================================================================

# All supported source types that use page markers
SOURCE_TYPES = [
    "PDF",      # PDF documents
    "TEXT",     # Plain text files
    "DOCX",     # Word documents
    "PPTX",     # PowerPoint presentations
    "IMAGE",    # Images (usually single page)
    "AUDIO",    # Audio transcriptions
    "LINK",     # Web URL content
    "YOUTUBE",  # YouTube video transcripts
]

# Human-readable display names for headers
SOURCE_TYPE_DISPLAY = {
    "PDF": "PDF document",
    "TEXT": "text file",
    "DOCX": "Word document",
    "PPTX": "PowerPoint presentation",
    "IMAGE": "image",
    "AUDIO": "audio file",
    "LINK": "URL",
    "YOUTUBE": "YouTube video transcript",
}


# =============================================================================
# MARKER FORMAT (for creating markers)
# =============================================================================

def build_page_marker(source_type: str, page_num: int, total_pages: int) -> str:
    """
    Build a page marker string.

    Args:
        source_type: Type of source (PDF, TEXT, DOCX, etc.)
        page_num: Current page number (1-indexed)
        total_pages: Total number of pages

    Returns:
        Formatted marker string like "=== PDF PAGE 1 of 5 ==="
    """
    return f"=== {source_type.upper()} PAGE {page_num} of {total_pages} ==="


# =============================================================================
# REGEX PATTERNS (for parsing markers)
# =============================================================================

# Pattern to match any page marker
# Captures: group(1) = page number, group(2) = total pages
# The .*? allows for optional suffixes like "(continues...)"
ANY_PAGE_PATTERN = re.compile(
    r'=== (?:PDF|TEXT|DOCX|PPTX|AUDIO|LINK|YOUTUBE|IMAGE) PAGE (\d+) of (\d+).*?==='
)

# Type-specific patterns (for when you need to match a specific type)
PAGE_PATTERNS = {
    "PDF": re.compile(r'=== PDF PAGE (\d+) of (\d+).*?==='),
    "TEXT": re.compile(r'=== TEXT PAGE (\d+) of (\d+) ==='),
    "DOCX": re.compile(r'=== DOCX PAGE (\d+) of (\d+) ==='),
    "PPTX": re.compile(r'=== PPTX PAGE (\d+) of (\d+).*?==='),
    "IMAGE": re.compile(r'=== IMAGE PAGE (\d+) of (\d+) ==='),
    "AUDIO": re.compile(r'=== AUDIO PAGE (\d+) of (\d+) ==='),
    "LINK": re.compile(r'=== LINK PAGE (\d+) of (\d+) ==='),
    "YOUTUBE": re.compile(r'=== YOUTUBE PAGE (\d+) of (\d+) ==='),
}


def find_all_markers(text: str) -> List[re.Match]:
    """
    Find all page markers in text.

    Args:
        text: The processed text content

    Returns:
        List of regex match objects for each marker found
    """
    return list(ANY_PAGE_PATTERN.finditer(text))


def get_page_number(match: re.Match) -> int:
    """Extract page number from a marker match."""
    return int(match.group(1))


def get_total_pages(match: re.Match) -> int:
    """Extract total pages from a marker match."""
    return int(match.group(2))
