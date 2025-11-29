"""
Text Utilities - Modular text processing for the RAG pipeline.

Educational Note: Text processing is central to RAG applications:
1. Cleaning: Prepare text for embeddings (remove noise, normalize whitespace)
2. Page Markers: Standardized format for marking page boundaries
3. Processed Output: Build standardized output format with page markers
4. Chunking: Parse processed text into token-based chunks for embeddings

All processed sources end up as .txt files with page markers like:
    === PDF PAGE 1 of 5 ===
    === DOCX PAGE 1 of 1 ===
    === YOUTUBE PAGE 1 of 1 ===

Sources with logical pages (PDF, PPTX) preserve their structure.
Sources without logical pages (TEXT, DOCX, AUDIO, LINK, YOUTUBE) use a single
page marker - token-based chunking handles the splitting for embeddings.

Modules:
- cleaning: Text cleaning functions for embeddings
- page_markers: Shared page marker format and patterns
- processed_output: Build and save standardized processed text output
- chunking: Parse processed text into chunks for embeddings
"""
# Cleaning utilities
from app.utils.text.cleaning import (
    clean_text_for_embedding,
    clean_chunk_text,
    normalize_whitespace
)

# Page marker utilities
from app.utils.text.page_markers import (
    SOURCE_TYPES,
    SOURCE_TYPE_DISPLAY,
    build_page_marker,
    ANY_PAGE_PATTERN,
    PAGE_PATTERNS,
    find_all_markers,
    get_page_number,
    get_total_pages
)

# Processed output utilities
from app.utils.text.processed_output import (
    SOURCE_METADATA_KEYS,
    build_processed_output,
    save_processed_text,
    build_and_save_processed_output
)

# Chunking utilities
from app.utils.text.chunking import (
    Chunk,
    parse_processed_text,
    parse_extracted_text,  # Backward compatibility alias
    chunks_to_pinecone_format,
    save_chunks_to_files,
    load_chunk_by_id,
    load_chunks_for_source,
    delete_chunks_for_source
)

__all__ = [
    # Cleaning
    "clean_text_for_embedding",
    "clean_chunk_text",
    "normalize_whitespace",
    # Page markers
    "SOURCE_TYPES",
    "SOURCE_TYPE_DISPLAY",
    "build_page_marker",
    "ANY_PAGE_PATTERN",
    "PAGE_PATTERNS",
    "find_all_markers",
    "get_page_number",
    "get_total_pages",
    # Processed output
    "SOURCE_METADATA_KEYS",
    "build_processed_output",
    "save_processed_text",
    "build_and_save_processed_output",
    # Chunking
    "Chunk",
    "parse_processed_text",
    "parse_extracted_text",
    "chunks_to_pinecone_format",
    "save_chunks_to_files",
    "load_chunk_by_id",
    "load_chunks_for_source",
    "delete_chunks_for_source",
]
