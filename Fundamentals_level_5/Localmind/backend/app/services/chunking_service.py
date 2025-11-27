"""
Chunking Service - Parse extracted text and split by pages.

Educational Note: For our PDF extraction, each page is already a logical chunk.
The extracted text file has page markers like:
    === PDF PAGE 1 of 10 ===

We parse these markers to split the content into page-based chunks.
Each chunk = one page, which provides:
- Natural content boundaries
- Easy citation (page numbers)
- Consistent chunk sizes for most documents

Chunk Storage:
Chunks are stored as individual .txt files in source-specific folders:
    data/projects/{project_id}/sources/chunks/{source_id}/{source_id}_chunk_{n}.txt

This structure allows:
- Easy retrieval by chunk_id when Pinecone returns search results
- Human-readable format for debugging
- Metadata preserved with content
- Simple cleanup: delete entire source folder when source is deleted
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Chunk:
    """
    Represents a text chunk (one page) with metadata.

    Educational Note: Storing metadata with chunks enables:
    - Citing page numbers in responses
    - Filtering search by source
    - Tracking which content came from where
    """
    text: str
    page_number: int
    source_id: str
    source_name: str
    chunk_id: str  # Unique ID for Pinecone: {source_id}_{page_number}


class ChunkingService:
    """
    Service for parsing extracted text into page-based chunks.

    Educational Note: Simple approach - one page = one chunk.
    The PDF extraction already handles the hard work of maintaining
    page boundaries and context across pages.
    """

    # Regex pattern to match page markers
    # Matches: === PDF PAGE 1 of 10 === or === PDF PAGE 1 of 10 (continues...)===
    PAGE_MARKER_PATTERN = r'=== PDF PAGE (\d+) of (\d+).*?==='

    def __init__(self):
        """Initialize the chunking service."""
        pass

    def parse_extracted_text(
        self,
        text: str,
        source_id: str,
        source_name: str
    ) -> List[Chunk]:
        """
        Parse extracted PDF text into page-based chunks.

        Educational Note: The extracted text format is:
            # Extracted from PDF: filename.pdf
            # Total pages: 10
            ...

            === PDF PAGE 1 of 10 ===

            [page 1 content]

            === PDF PAGE 2 of 10 ===

            [page 2 content]
            ...

        Args:
            text: The full extracted text content
            source_id: UUID of the source document
            source_name: Display name of the source

        Returns:
            List of Chunk objects, one per page
        """
        if not text:
            return []

        chunks = []

        # Find all page markers and their positions
        markers = list(re.finditer(self.PAGE_MARKER_PATTERN, text))

        if not markers:
            # No page markers found - treat entire text as one chunk
            clean_text = self._clean_text(text)
            if clean_text:
                chunks.append(Chunk(
                    text=clean_text,
                    page_number=1,
                    source_id=source_id,
                    source_name=source_name,
                    chunk_id=f"{source_id}_page_1"
                ))
            return chunks

        # Extract content between page markers
        for i, marker in enumerate(markers):
            page_number = int(marker.group(1))

            # Content starts after this marker
            content_start = marker.end()

            # Content ends at next marker or end of text
            if i + 1 < len(markers):
                content_end = markers[i + 1].start()
            else:
                content_end = len(text)

            # Extract and clean the page content
            page_content = text[content_start:content_end]
            clean_content = self._clean_text(page_content)

            if clean_content:  # Only add non-empty chunks
                chunks.append(Chunk(
                    text=clean_content,
                    page_number=page_number,
                    source_id=source_id,
                    source_name=source_name,
                    chunk_id=f"{source_id}_page_{page_number}"
                ))

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Strip leading/trailing whitespace
        text = text.strip()

        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        return text

    def chunks_to_pinecone_format(
        self,
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
                    "source_id": chunk.source_id,
                    "source_name": chunk.source_name,
                }
            })

        return vectors

    def save_chunks_to_files(
        self,
        chunks: List[Chunk],
        chunks_dir: Path
    ) -> List[str]:
        """
        Save chunks as individual .txt files in source-specific folder.

        Educational Note: Each chunk is saved as a separate file with
        metadata header. Chunks are organized by source_id folder for
        easier management.

        Structure:
            chunks_dir/{source_id}/{source_id}_chunk_{n}.txt

        File format:
            # Chunk Metadata
            # source_id: {source_id}
            # source_name: {source_name}
            # chunk_number: {number}
            # page_number: {page_number}
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
        self,
        chunk_id: str,
        chunks_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Load a chunk by its ID from the chunks directory.

        Educational Note: When Pinecone returns search results, we get
        chunk IDs. We use this method to load the actual text content
        for those chunks to pass to the AI.

        Structure:
            chunks_dir/{source_id}/{source_id}_chunk_{n}.txt

        Args:
            chunk_id: The chunk ID (e.g., "{source_id}_page_{number}")
            chunks_dir: Base chunks directory

        Returns:
            Dict with chunk metadata and text, or None if not found
        """
        # chunk_id format: {source_id}_page_{page_number}
        # Extract source_id to find the right folder
        source_id = chunk_id.rsplit('_page_', 1)[0] if '_page_' in chunk_id else chunk_id

        # Look in source-specific folder
        source_chunks_dir = chunks_dir / source_id
        if not source_chunks_dir.exists():
            return None

        # Search for the file containing this chunk_id
        for file_path in source_chunks_dir.glob(f"{source_id}_chunk_*.txt"):
            chunk_data = self._parse_chunk_file(file_path)
            if chunk_data and chunk_data.get('chunk_id') == chunk_id:
                return chunk_data

        return None

    def load_chunks_for_source(
        self,
        source_id: str,
        chunks_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Load all chunks for a specific source.

        Structure:
            chunks_dir/{source_id}/{source_id}_chunk_{n}.txt

        Args:
            source_id: The source UUID
            chunks_dir: Base chunks directory

        Returns:
            List of chunk dicts with metadata and text
        """
        # Look in source-specific folder
        source_chunks_dir = chunks_dir / source_id
        if not source_chunks_dir.exists():
            return []

        chunks = []
        for file_path in sorted(source_chunks_dir.glob(f"{source_id}_chunk_*.txt")):
            chunk_data = self._parse_chunk_file(file_path)
            if chunk_data:
                chunks.append(chunk_data)

        return chunks

    def _parse_chunk_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
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
                'chunk_id': metadata.get('chunk_id'),
                'created_at': metadata.get('created_at'),
                'text': text_part.strip(),
                'file_path': str(file_path)
            }
        except Exception as e:
            print(f"Error parsing chunk file {file_path}: {e}")
            return None

    def delete_chunks_for_source(
        self,
        source_id: str,
        chunks_dir: Path
    ) -> int:
        """
        Delete all chunk files for a specific source.

        Educational Note: When a source is deleted, we delete the entire
        source folder containing all its chunk files.

        Structure:
            chunks_dir/{source_id}/ (entire folder deleted)

        Args:
            source_id: The source UUID
            chunks_dir: Base chunks directory

        Returns:
            Number of files deleted
        """
        import shutil

        # Look in source-specific folder
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


# Singleton instance for easy import
chunking_service = ChunkingService()
