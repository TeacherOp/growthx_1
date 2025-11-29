"""
Chunking - Parse processed text into token-based chunks for embeddings.

Educational Note: This module handles the final step of source processing:
converting processed text (with page markers) into individual chunks that
can be embedded and stored in Pinecone.

Pipeline:
1. Source processed → text with page markers (=== PDF PAGE 1 of 5 ===)
2. This module parses markers → extracts content per page
3. Each page is split into ~200 token chunks (±20% = 160-240 tokens)
4. Chunks are embedded and stored in Pinecone
5. Chunks are also saved as individual .txt files for retrieval

Token-Based Chunking:
- Target: 200 tokens per chunk
- Margin: ±20% (160-240 token range)
- Small sources (< 240 tokens) → 1 chunk (whole content)
- Large pages → split into multiple chunks

Chunk ID Format:
- Single chunk from page: {source_id}_page_{page}_chunk_1
- Multiple chunks from page: {source_id}_page_{page}_chunk_{n}

This allows:
- Semantic search with properly sized chunks
- Citation back to source page
- Consistent chunk sizes across all source types
"""
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from app.utils.text.cleaning import clean_text_for_embedding
from app.utils.text.page_markers import ANY_PAGE_PATTERN, find_all_markers, get_page_number
from app.utils.embedding_utils import count_tokens, get_chunk_config


@dataclass
class Chunk:
    """
    Represents a text chunk with metadata for RAG.

    Educational Note: Storing metadata with chunks enables:
    - Citing page numbers in responses
    - Filtering search by source
    - Tracking which content came from where
    - Supporting multiple chunks per page
    """
    text: str
    page_number: int
    source_id: str
    source_name: str
    chunk_id: str  # Unique ID: {source_id}_page_{page}_chunk_{n}
    chunk_index: int = 1  # Which chunk within this page (1-indexed)


def parse_processed_text(
    text: str,
    source_id: str,
    source_name: str
) -> List[Chunk]:
    """
    Parse processed text (with page markers) into token-based chunks.

    Educational Note: This function handles all source types (PDF, TEXT, DOCX,
    PPTX, AUDIO, LINK, YOUTUBE, IMAGE). The page markers follow a consistent
    format: === {TYPE} PAGE {N} of {TOTAL} ===

    Token-Based Chunking:
    - Each page's content is split into ~200 token chunks
    - Small pages (< 240 tokens) become 1 chunk
    - Large pages are split into multiple chunks
    - Each chunk maintains reference to original page for citations

    Args:
        text: The full processed text content with page markers
        source_id: UUID of the source document
        source_name: Display name of the source

    Returns:
        List of Chunk objects (may have multiple chunks per page)
    """
    if not text:
        return []

    chunks = []

    # Find all page markers
    markers = find_all_markers(text)

    if not markers:
        # No page markers found - treat entire text as source to chunk
        clean_text = clean_text_for_embedding(text)
        if clean_text:
            page_chunks = _split_text_into_token_chunks(clean_text)
            for i, chunk_text in enumerate(page_chunks, start=1):
                chunks.append(Chunk(
                    text=chunk_text,
                    page_number=1,
                    source_id=source_id,
                    source_name=source_name,
                    chunk_id=f"{source_id}_page_1_chunk_{i}",
                    chunk_index=i
                ))
        return chunks

    # Extract content between page markers and split into token-based chunks
    for i, marker in enumerate(markers):
        page_number = get_page_number(marker)

        # Content starts after this marker
        content_start = marker.end()

        # Content ends at next marker or end of text
        if i + 1 < len(markers):
            content_end = markers[i + 1].start()
        else:
            content_end = len(text)

        # Extract and clean the page content
        page_content = text[content_start:content_end]
        clean_content = clean_text_for_embedding(page_content)

        if clean_content:
            # Split page into token-based chunks
            page_chunks = _split_text_into_token_chunks(clean_content)

            for chunk_idx, chunk_text in enumerate(page_chunks, start=1):
                chunks.append(Chunk(
                    text=chunk_text,
                    page_number=page_number,
                    source_id=source_id,
                    source_name=source_name,
                    chunk_id=f"{source_id}_page_{page_number}_chunk_{chunk_idx}",
                    chunk_index=chunk_idx
                ))

    return chunks


def _split_text_into_token_chunks(text: str) -> List[str]:
    """
    Split text into chunks based on token count.

    Educational Note: We target ~200 tokens per chunk with ±20% margin.
    This ensures chunks are:
    - Small enough for effective semantic search
    - Large enough to maintain context
    - Consistent across all source types

    Split Strategy:
    1. If text <= max_tokens (240): Return as single chunk
    2. Otherwise: Split at sentence boundaries near target_tokens (200)
    3. Fallback: Split at word boundaries if no sentences found

    Args:
        text: Clean text to split into chunks

    Returns:
        List of chunk strings
    """
    if not text:
        return []

    config = get_chunk_config()
    target_tokens = config["target_tokens"]  # 200
    max_tokens = config["max_tokens"]  # 240

    # Check if text fits in one chunk
    total_tokens = count_tokens(text)
    if total_tokens <= max_tokens:
        return [text]

    # Need to split - use sentence-based splitting
    chunks = []
    sentences = _split_into_sentences(text)

    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        # If single sentence exceeds max, split by words
        if sentence_tokens > max_tokens:
            # First, save current chunk if any
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            # Split long sentence by words
            word_chunks = _split_long_sentence(sentence, target_tokens, max_tokens)
            chunks.extend(word_chunks)
            continue

        # Check if adding this sentence exceeds target
        if current_tokens + sentence_tokens > target_tokens:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_tokens = sentence_tokens
        else:
            # Add to current chunk
            current_chunk.append(sentence)
            current_tokens += sentence_tokens

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences for chunk boundary detection.

    Educational Note: We split at sentence boundaries to maintain
    semantic coherence within chunks. A sentence ending is detected
    by . ! or ? followed by space or end of text.

    Args:
        text: Text to split into sentences

    Returns:
        List of sentences
    """
    import re

    # Split on sentence endings followed by space or end
    # Keeps the punctuation with the sentence
    pattern = r'(?<=[.!?])\s+'
    sentences = re.split(pattern, text)

    # Filter empty and clean whitespace
    return [s.strip() for s in sentences if s.strip()]


def _split_long_sentence(sentence: str, target_tokens: int, max_tokens: int) -> List[str]:
    """
    Split a long sentence by words when it exceeds max_tokens.

    Educational Note: This is a fallback for very long sentences
    (like run-on sentences or lists). We split at word boundaries
    to avoid breaking mid-word.

    Args:
        sentence: Long sentence to split
        target_tokens: Target tokens per chunk (200)
        max_tokens: Maximum tokens per chunk (240)

    Returns:
        List of chunk strings
    """
    words = sentence.split()
    chunks = []
    current_words = []
    current_tokens = 0

    for word in words:
        word_tokens = count_tokens(word)

        if current_tokens + word_tokens > target_tokens and current_words:
            # Save current chunk and start new one
            chunks.append(" ".join(current_words))
            current_words = [word]
            current_tokens = word_tokens
        else:
            current_words.append(word)
            current_tokens += word_tokens

    # Don't forget last chunk
    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def chunks_to_pinecone_format(
    chunks: List[Chunk],
    embeddings: List[List[float]]
) -> List[Dict[str, Any]]:
    """
    Convert chunks to Pinecone upsert format.

    Educational Note: Pinecone expects vectors in this format:
    {
        "id": "unique_id",
        "values": [0.1, 0.2, ...],  # The embedding vector
        "metadata": {...}  # Searchable/filterable metadata
    }

    Metadata includes:
    - text: The chunk text for retrieval
    - page_number: Original page for citations
    - chunk_index: Which chunk within the page (for ordering)
    - source_id/source_name: For filtering by source

    Args:
        chunks: List of Chunk objects
        embeddings: List of embedding vectors (same order as chunks)

    Returns:
        List of dicts ready for Pinecone upsert
    """
    if len(chunks) != len(embeddings):
        raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch")

    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vectors.append({
            "id": chunk.chunk_id,
            "values": embedding,
            "metadata": {
                "text": chunk.text,  # Store text for retrieval
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,  # Which chunk within page
                "source_id": chunk.source_id,
                "source_name": chunk.source_name,
            }
        })

    return vectors


def save_chunks_to_files(
    chunks: List[Chunk],
    chunks_dir: Path
) -> List[str]:
    """
    Save chunks as individual .txt files in source-specific folder.

    Educational Note: Each chunk is saved as a separate file with
    metadata header. Chunks are organized by source_id folder.

    Structure:
        chunks_dir/{source_id}/{source_id}_chunk_{n}.txt

    File format:
        # Chunk Metadata
        # source_id: {source_id}
        # source_name: {source_name}
        # chunk_number: {number}  (global index across all chunks)
        # page_number: {page_number}  (original page for citations)
        # chunk_index: {index}  (chunk index within page)
        # chunk_id: {chunk_id}
        # created_at: {timestamp}
        # ---

        [chunk text content]

    Args:
        chunks: List of Chunk objects to save
        chunks_dir: Base chunks directory

    Returns:
        List of saved file paths
    """
    if not chunks:
        return []

    # Get source_id from first chunk (all chunks belong to same source)
    source_id = chunks[0].source_id

    # Create source-specific directory: chunks_dir/{source_id}/
    source_chunks_dir = chunks_dir / source_id
    source_chunks_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    timestamp = datetime.now().isoformat()

    for i, chunk in enumerate(chunks, start=1):
        # Create filename: {source_id}_chunk_{number}.txt
        filename = f"{chunk.source_id}_chunk_{i}.txt"
        file_path = source_chunks_dir / filename

        # Build file content with metadata header
        content = f"""# Chunk Metadata
# source_id: {chunk.source_id}
# source_name: {chunk.source_name}
# chunk_number: {i}
# page_number: {chunk.page_number}
# chunk_index: {chunk.chunk_index}
# chunk_id: {chunk.chunk_id}
# created_at: {timestamp}
# ---

{chunk.text}
"""
        # Save the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        saved_paths.append(str(file_path))

    return saved_paths


def load_chunk_by_id(
    chunk_id: str,
    chunks_dir: Path
) -> Optional[Dict[str, Any]]:
    """
    Load a chunk by its ID from the chunks directory.

    Educational Note: When Pinecone returns search results, we get
    chunk IDs. We use this function to load the actual text content.

    Chunk ID Format: {source_id}_page_{page}_chunk_{n}
    Example: abc123_page_1_chunk_2

    Args:
        chunk_id: The chunk ID
        chunks_dir: Base chunks directory

    Returns:
        Dict with chunk metadata and text, or None if not found
    """
    # chunk_id format: {source_id}_page_{page}_chunk_{n}
    # Extract source_id (everything before first _page_)
    if '_page_' in chunk_id:
        source_id = chunk_id.split('_page_')[0]
    else:
        source_id = chunk_id

    # Look in source-specific folder
    source_chunks_dir = chunks_dir / source_id
    if not source_chunks_dir.exists():
        return None

    # Search for the file containing this chunk_id
    for file_path in source_chunks_dir.glob(f"{source_id}_chunk_*.txt"):
        chunk_data = _parse_chunk_file(file_path)
        if chunk_data and chunk_data.get('chunk_id') == chunk_id:
            return chunk_data

    return None


def load_chunks_for_source(
    source_id: str,
    chunks_dir: Path
) -> List[Dict[str, Any]]:
    """
    Load all chunks for a specific source.

    Args:
        source_id: The source UUID
        chunks_dir: Base chunks directory

    Returns:
        List of chunk dicts with metadata and text
    """
    source_chunks_dir = chunks_dir / source_id
    if not source_chunks_dir.exists():
        return []

    chunks = []
    for file_path in sorted(source_chunks_dir.glob(f"{source_id}_chunk_*.txt")):
        chunk_data = _parse_chunk_file(file_path)
        if chunk_data:
            chunks.append(chunk_data)

    return chunks


def _parse_chunk_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse a chunk file and extract metadata + text.

    Args:
        file_path: Path to the chunk .txt file

    Returns:
        Dict with metadata and text, or None if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split header and content
        if '# ---' not in content:
            return None

        header_part, text_part = content.split('# ---', 1)

        # Parse metadata from header
        metadata = {}
        for line in header_part.strip().split('\n'):
            if line.startswith('# ') and ': ' in line:
                key, value = line[2:].split(': ', 1)
                metadata[key] = value

        return {
            'source_id': metadata.get('source_id'),
            'source_name': metadata.get('source_name'),
            'chunk_number': int(metadata.get('chunk_number', 0)),
            'page_number': int(metadata.get('page_number', 0)),
            'chunk_index': int(metadata.get('chunk_index', 1)),  # Default to 1 for old files
            'chunk_id': metadata.get('chunk_id'),
            'created_at': metadata.get('created_at'),
            'text': text_part.strip(),
            'file_path': str(file_path)
        }
    except Exception as e:
        print(f"Error parsing chunk file {file_path}: {e}")
        return None


def delete_chunks_for_source(
    source_id: str,
    chunks_dir: Path
) -> int:
    """
    Delete all chunk files for a specific source.

    Educational Note: When a source is deleted, we delete the entire
    source folder containing all its chunk files.

    Args:
        source_id: The source UUID
        chunks_dir: Base chunks directory

    Returns:
        Number of files deleted
    """
    source_chunks_dir = chunks_dir / source_id
    if not source_chunks_dir.exists():
        return 0

    # Count files before deletion
    deleted_count = len(list(source_chunks_dir.glob("*.txt")))

    # Delete entire source folder
    try:
        shutil.rmtree(source_chunks_dir)
    except Exception as e:
        print(f"Error deleting chunks folder {source_chunks_dir}: {e}")
        return 0

    return deleted_count


# Backward compatibility alias
parse_extracted_text = parse_processed_text
