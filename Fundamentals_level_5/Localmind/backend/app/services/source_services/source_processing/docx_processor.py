"""
DOCX Processor - Handles Word document processing.

Educational Note: DOCX files are processed using python-docx library.
The extracted text preserves document structure (headings, lists, tables)
in a markdown-like format. DOCX files don't have logical page boundaries,
so we store the entire content as a single "page" and let token-based
chunking handle the splitting for embeddings.

This creates a single page marker: === DOCX PAGE 1 of 1 ===
Token-based chunking then splits into ~200 token chunks for embeddings.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.utils.docx_utils import extract_text_from_docx
from app.utils.text import build_processed_output
from app.utils.path_utils import get_processed_dir, get_chunks_dir
from app.utils.embedding_utils import needs_embedding, count_tokens
from app.services.ai_services.embedding_service import embedding_service
from app.services.ai_services.summary_service import summary_service


def process_docx(
    project_id: str,
    source_id: str,
    source: Dict[str, Any],
    raw_file_path: Path,
    source_service
) -> Dict[str, Any]:
    """
    Process a DOCX file - extract text and save to processed folder.

    Args:
        project_id: The project UUID
        source_id: The source UUID
        source: Source metadata dict
        raw_file_path: Path to the raw DOCX file
        source_service: Reference to source_service for updates

    Returns:
        Dict with success status
    """
    # Extract text from DOCX
    result = extract_text_from_docx(raw_file_path)

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

    # DOCX files don't have logical page boundaries
    # Pass entire content as single page, let token-based chunking handle splits
    pages = [content]

    # Calculate token count for metadata
    token_count = count_tokens(content)

    # Build metadata for DOCX type
    metadata = {
        "paragraph_count": result.get("paragraph_count", 0),
        "table_count": result.get("table_count", 0),
        "character_count": len(content),
        "token_count": token_count
    }

    # Use centralized build_processed_output for consistent format
    processed_content = build_processed_output(
        pages=pages,
        source_type="DOCX",
        source_name=source_name,
        metadata=metadata
    )

    # Save processed content
    processed_dir = get_processed_dir(project_id)
    processed_path = processed_dir / f"{source_id}.txt"
    with open(processed_path, "w", encoding="utf-8") as f:
        f.write(processed_content)

    processing_info = {
        "processor": "docx_processor",
        "paragraph_count": result.get("paragraph_count", 0),
        "table_count": result.get("table_count", 0),
        "character_count": len(content),
        "token_count": token_count,
        "total_pages": 1,
        "extracted_at": datetime.now().isoformat()
    }

    # Process embeddings if needed
    embedding_info = _process_embeddings(
        project_id=project_id,
        source_id=source_id,
        source_name=source_name,
        processed_text=processed_content,
        source_service=source_service
    )

    # Generate summary after embeddings
    source_metadata = {**source, "processing_info": processing_info, "embedding_info": embedding_info}
    summary_info = _generate_summary(project_id, source_id, source_metadata)

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


def _process_embeddings(
    project_id: str,
    source_id: str,
    source_name: str,
    processed_text: str,
    source_service
) -> Dict[str, Any]:
    """
    Process embeddings for a source using embedding_service.

    Educational Note: We ALWAYS chunk and embed every source for consistent
    retrieval. The token count is used for chunk sizing decisions.
    """
    try:
        # Get embedding info (always embeds, token count used for chunking)
        _, token_count, reason = needs_embedding(text=processed_text)

        source_service.update_source(project_id, source_id, status="embedding")
        print(f"Starting embedding for {source_name} ({reason})")

        chunks_dir = get_chunks_dir(project_id)
        return embedding_service.process_embeddings(
            project_id=project_id,
            source_id=source_id,
            source_name=source_name,
            processed_text=processed_text,
            chunks_dir=chunks_dir
        )

    except Exception as e:
        print(f"Error processing embeddings for {source_id}: {e}")
        return {
            "is_embedded": False,
            "embedded_at": None,
            "token_count": 0,
            "chunk_count": 0,
            "reason": f"Embedding error: {str(e)}"
        }


def _generate_summary(
    project_id: str,
    source_id: str,
    source_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate a summary for a processed source."""
    try:
        print(f"Generating summary for source: {source_id}")
        result = summary_service.generate_summary(
            project_id=project_id,
            source_id=source_id,
            source_metadata=source_metadata
        )
        if result:
            print(f"Summary generated for {source_id}: {len(result.get('summary', ''))} chars")
            return result
        return {}
    except Exception as e:
        print(f"Error generating summary for {source_id}: {e}")
        return {}
