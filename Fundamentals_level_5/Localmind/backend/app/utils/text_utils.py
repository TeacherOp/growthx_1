"""
Text Utilities - Common text cleaning and processing functions.

Educational Note: Clean text is important for:
- Embeddings: Excessive whitespace/newlines reduce embedding quality
- Token counting: Clean text gives more accurate counts
- Storage: Smaller file sizes without redundant whitespace
- Display: Better readability in UI

This utility provides reusable functions for text cleaning across services.
"""
import re


def clean_text_for_embedding(text: str) -> str:
    """
    Clean text before creating embeddings.

    Educational Note: OpenAI embeddings work best with clean text.
    Excessive whitespace and newlines add noise without semantic value.

    Cleaning steps:
    1. Strip leading/trailing whitespace
    2. Replace multiple newlines with single newline
    3. Replace multiple spaces with single space
    4. Final trim

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text ready for embedding
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # Replace multiple newlines with single newline
    text = re.sub(r'\n{2,}', '\n', text)

    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)

    # Final trim
    text = text.strip()

    return text


def clean_chunk_text(text: str) -> str:
    """
    Clean chunk text, removing metadata headers if present.

    Educational Note: Our chunk files have metadata headers like:
        # Chunk Metadata
        # source_id: ...
        # ---

        [actual content]

    This function removes the header and cleans the remaining text.

    Args:
        text: Raw chunk text (may include metadata header)

    Returns:
        Cleaned text without metadata header
    """
    if not text:
        return ""

    # Remove metadata header if present
    # Header format: # Chunk Metadata ... # ---
    if text.startswith("# Chunk Metadata"):
        header_end = text.find("# ---")
        if header_end != -1:
            text = text[header_end + 5:]  # Skip past "# ---"

    # Apply standard embedding cleaning
    return clean_text_for_embedding(text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace without being as aggressive as embedding cleaning.

    Educational Note: Sometimes we want to preserve paragraph breaks
    (double newlines) but still clean up excessive whitespace.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # Replace 3+ newlines with double newline (preserve paragraphs)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)

    return text


