"""
Summary Service - Generate concise summaries for processed sources.

Educational Note: This service generates summaries for source documents
after processing is complete. It uses a smart sampling strategy to handle
documents of varying sizes while keeping API costs low.

Summary Strategy:
- Small sources (not chunked, <2500 tokens): Send entire content
- Large sources (chunked): Send evenly distributed sample of chunks
- Input budget: ~20k tokens max (8 chunks at ~2500 tokens each)
- Output: 150-200 tokens summary

The summary is stored in the source index under the 'summary' field.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from config import Config
from app.services.claude_service import claude_service
from app.services.chunking_service import chunking_service


class SummaryService:
    """
    Service for generating source summaries.

    Educational Note: Uses Haiku model for cost-effective summarization.
    Input: $1/M tokens, Output: $3/M tokens
    ~20k input + 200 output = ~$0.02 per summary
    """

    # Maximum chunks to send for summarization (budget: ~20k tokens)
    MAX_CHUNKS = 8

    def __init__(self):
        """Initialize the summary service."""
        self.projects_dir = Config.PROJECTS_DIR
        self.prompts_dir = Config.DATA_DIR / "prompts"
        self._prompt_config: Optional[Dict[str, Any]] = None

    def _load_prompt_config(self) -> Dict[str, Any]:
        """
        Load the summary prompt configuration.

        Returns:
            Dict with system_prompt, model, max_tokens, temperature
        """
        if self._prompt_config is None:
            prompt_path = self.prompts_dir / "summary_prompt.json"

            if not prompt_path.exists():
                raise FileNotFoundError(f"Summary prompt not found: {prompt_path}")

            with open(prompt_path, 'r') as f:
                self._prompt_config = json.load(f)

        return self._prompt_config

    def _get_processed_dir(self, project_id: str) -> Path:
        """Get the processed files directory for a project."""
        return self.projects_dir / project_id / "sources" / "processed"

    def _get_chunks_dir(self, project_id: str) -> Path:
        """Get the chunks directory for a project."""
        return self.projects_dir / project_id / "sources" / "chunks"

    def _get_chunk_indices(self, total_chunks: int, chunks_to_select: int) -> List[int]:
        """
        Get evenly distributed chunk indices, always including first and last.

        Educational Note: Uses linear interpolation to distribute selection.
        Formula: index[i] = round(i * (total - 1) / (select - 1))

        This ensures:
        - First chunk (intro/context) is always included
        - Last chunk (conclusion) is always included
        - Middle chunks are evenly spaced

        Args:
            total_chunks: Total number of chunks available
            chunks_to_select: Number of chunks to select

        Returns:
            List of chunk indices (0-based)
        """
        if chunks_to_select >= total_chunks:
            return list(range(total_chunks))

        if chunks_to_select == 1:
            return [0]

        if chunks_to_select == 2:
            return [0, total_chunks - 1]

        # Calculate step size for even distribution
        step = (total_chunks - 1) / (chunks_to_select - 1)

        # Generate indices
        indices = [round(i * step) for i in range(chunks_to_select)]

        return indices

    def _load_processed_content(self, project_id: str, source_id: str) -> Optional[str]:
        """
        Load the full processed content for a source.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Processed text content or None if not found
        """
        processed_dir = self._get_processed_dir(project_id)
        processed_file = processed_dir / f"{source_id}.txt"

        if not processed_file.exists():
            return None

        with open(processed_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_selected_chunks(
        self,
        project_id: str,
        source_id: str
    ) -> Optional[str]:
        """
        Load evenly distributed chunks and concatenate them.

        Educational Note: For large documents, we select a sample of chunks
        to stay within our token budget while maintaining coverage of the
        document's content from beginning to end.

        Args:
            project_id: The project UUID
            source_id: The source UUID

        Returns:
            Concatenated chunk content with separators, or None if failed
        """
        chunks_dir = self._get_chunks_dir(project_id)

        # Load all chunks for this source
        all_chunks = chunking_service.load_chunks_for_source(source_id, chunks_dir)

        if not all_chunks:
            return None

        # Determine how many chunks to select
        chunks_to_select = min(self.MAX_CHUNKS, len(all_chunks))

        # Get evenly distributed indices
        indices = self._get_chunk_indices(len(all_chunks), chunks_to_select)

        # Build content from selected chunks
        content_parts = []
        for idx in indices:
            if idx < len(all_chunks):
                chunk = all_chunks[idx]
                page_num = chunk.get('page_number', idx + 1)
                content_parts.append(f"[Page {page_num}]\n{chunk['text']}")

        return "\n\n---\n\n".join(content_parts)

    def _build_user_message(
        self,
        content: str,
        source_metadata: Dict[str, Any],
        is_sampled: bool,
        total_pages: int,
        pages_sent: int
    ) -> str:
        """
        Build the user message with context about the document.

        Educational Note: Providing context about the document helps the AI
        generate a more appropriate summary. We include:
        - Document type (PDF, link, audio, etc.)
        - Original filename/URL
        - Whether content is sampled or complete
        - Total vs sent pages ratio

        Args:
            content: The content to summarize
            source_metadata: Source metadata from index
            is_sampled: Whether content is a sample (not full document)
            total_pages: Total pages/chunks in the document
            pages_sent: Number of pages/chunks being sent

        Returns:
            Formatted user message
        """
        category = source_metadata.get('category', 'document')
        name = source_metadata.get('name', 'Unknown')
        file_ext = source_metadata.get('file_extension', '')

        # Build context header
        context_lines = [
            f"Document Type: {category.upper()} ({file_ext})",
            f"Document Name: {name}",
            f"Total Document Length: {total_pages} pages/sections",
        ]

        if is_sampled:
            context_lines.append(
                f"Content Provided: {pages_sent} pages sampled at equal intervals "
                f"(pages include beginning, end, and evenly distributed middle sections)"
            )
        else:
            context_lines.append(f"Content Provided: Full document ({pages_sent} pages)")

        context = "\n".join(context_lines)

        return f"""DOCUMENT CONTEXT:
{context}

DOCUMENT CONTENT:
{content}"""

    def generate_summary(
        self,
        project_id: str,
        source_id: str,
        source_metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a summary for a processed source.

        Educational Note: This is the main entry point for summary generation.
        It determines the best strategy based on whether the source is chunked,
        loads the appropriate content, and calls the AI for summarization.

        Args:
            project_id: The project UUID
            source_id: The source UUID
            source_metadata: Source metadata from the index

        Returns:
            Dict with summary and metadata, or None if failed:
            {
                "summary": "The summary text...",
                "model": "claude-haiku-4-5-20250514",
                "usage": {"input_tokens": X, "output_tokens": Y},
                "generated_at": "2025-11-29T...",
                "strategy": "full" | "sampled",
                "pages_used": N
            }
        """
        # Load prompt configuration
        prompt_config = self._load_prompt_config()

        # Check if source is embedded (has chunks)
        embedding_info = source_metadata.get('embedding_info', {})
        is_embedded = embedding_info.get('is_embedded', False)
        chunk_count = embedding_info.get('chunk_count', 0)

        # Get total pages from processing_info
        processing_info = source_metadata.get('processing_info', {})
        total_pages = processing_info.get('total_pages', 1)

        # Determine content loading strategy
        if is_embedded and chunk_count > 0:
            # Source has chunks - use sampling strategy
            content = self._load_selected_chunks(project_id, source_id)
            is_sampled = chunk_count > self.MAX_CHUNKS
            pages_sent = min(self.MAX_CHUNKS, chunk_count)
        else:
            # Source is not chunked - send full processed content
            content = self._load_processed_content(project_id, source_id)
            is_sampled = False
            pages_sent = total_pages

        if not content:
            print(f"No content found for source {source_id}")
            return None

        # Build user message with context
        user_message = self._build_user_message(
            content=content,
            source_metadata=source_metadata,
            is_sampled=is_sampled,
            total_pages=total_pages,
            pages_sent=pages_sent
        )

        # Call Claude API
        try:
            response = claude_service.send_message(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=prompt_config.get('system_prompt'),
                model=prompt_config.get('model', 'claude-haiku-4-5-20250514'),
                max_tokens=prompt_config.get('max_tokens', 250),
                temperature=prompt_config.get('temperature', 0.3),
                project_id=project_id
            )

            summary_text = response.get('content', '').strip()

            if not summary_text:
                print(f"Empty summary returned for source {source_id}")
                return None

            from datetime import datetime

            return {
                "summary": summary_text,
                "model": response.get('model'),
                "usage": response.get('usage'),
                "generated_at": datetime.now().isoformat(),
                "strategy": "sampled" if is_sampled else "full",
                "pages_used": pages_sent,
                "total_pages": total_pages
            }

        except Exception as e:
            print(f"Error generating summary for source {source_id}: {e}")
            return None


# Singleton instance for easy import
summary_service = SummaryService()
