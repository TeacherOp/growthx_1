"""
Source Search Executor - Executes source search tool calls.

Educational Note: This service handles the search_sources tool execution:
1. For non-embedded sources: Returns full processed content
2. For embedded sources: Performs semantic search via Pinecone

The executor is called by main_chat_service when Claude uses the
search_sources tool. Results are returned as tool_result messages.
"""
from pathlib import Path
from typing import Dict, Any, Optional

from config import Config
from app.services.source_service import source_service
from app.services.openai_service import openai_service
from app.services.pinecone_service import pinecone_service


class SourceSearchExecutor:
    """
    Executor for source search tool calls.

    Educational Note: This class handles two search modes:
    1. Direct content retrieval (non-embedded sources)
    2. Semantic search (embedded sources with Pinecone)
    """

    # Number of chunks to return for semantic search
    DEFAULT_TOP_K = 5

    def __init__(self):
        """Initialize the executor."""
        self.projects_dir = Config.PROJECTS_DIR

    def execute(
        self,
        project_id: str,
        source_id: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a source search.

        Educational Note: This is the main entry point called by main_chat_service.
        It determines the search mode based on whether the source is embedded.

        Args:
            project_id: The project UUID
            source_id: The source UUID to search
            query: Optional search query (required for embedded sources)

        Returns:
            Dict with search results:
            {
                "success": True/False,
                "source_name": "filename.pdf",
                "content": "...",  # Full content or search results
                "search_type": "full_content" | "semantic_search",
                "error": "..." (if success is False)
            }
        """
        # Get source metadata
        source = source_service.get_source(project_id, source_id)

        if not source:
            return {
                "success": False,
                "error": f"Source not found: {source_id}"
            }

        # Check if source is ready and active
        if source.get("status") != "ready":
            return {
                "success": False,
                "error": f"Source is not ready (status: {source.get('status')})"
            }

        if not source.get("active", False):
            return {
                "success": False,
                "error": "Source is not active"
            }

        # Check if embedded
        embedding_info = source.get("embedding_info", {})
        is_embedded = embedding_info.get("is_embedded", False)

        if is_embedded:
            return self._semantic_search(project_id, source_id, source, query)
        else:
            return self._get_full_content(project_id, source_id, source)

    def _get_full_content(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get full processed content for a non-embedded source.

        Educational Note: For small sources that weren't embedded,
        we return the entire processed text file. This is efficient
        because these sources are under the embedding threshold.

        Args:
            project_id: The project UUID
            source_id: The source UUID
            source: Source metadata dict

        Returns:
            Dict with full content
        """
        processed_path = self.projects_dir / project_id / "sources" / "processed" / f"{source_id}.txt"

        if not processed_path.exists():
            return {
                "success": False,
                "error": "Processed content file not found"
            }

        try:
            with open(processed_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "source_name": source.get("name", "Unknown"),
                "source_id": source_id,
                "content": content,
                "search_type": "full_content",
                "character_count": len(content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading content: {str(e)}"
            }

    def _semantic_search(
        self,
        project_id: str,
        source_id: str,
        source: Dict[str, Any],
        query: Optional[str]
    ) -> Dict[str, Any]:
        """
        Perform semantic search on an embedded source.

        Educational Note: For large embedded sources:
        1. Convert query to embedding using OpenAI
        2. Search Pinecone for similar chunks (filtered by source_id)
        3. Return top matching chunks with their text

        Args:
            project_id: The project UUID
            source_id: The source UUID
            source: Source metadata dict
            query: Search query (required)

        Returns:
            Dict with search results
        """
        if not query:
            return {
                "success": False,
                "error": "Query is required for embedded sources (semantic search)"
            }

        try:
            # Check if services are configured
            if not pinecone_service.is_configured():
                return {
                    "success": False,
                    "error": "Pinecone is not configured. Please add API key in settings."
                }

            # Create query embedding
            query_vector = openai_service.create_embedding(query)

            # Search Pinecone with source_id filter
            results = pinecone_service.search(
                query_vector=query_vector,
                namespace=project_id,
                top_k=self.DEFAULT_TOP_K,
                filter={"source_id": {"$eq": source_id}},
                include_metadata=True
            )

            if not results:
                return {
                    "success": True,
                    "source_name": source.get("name", "Unknown"),
                    "source_id": source_id,
                    "content": "No matching content found for the query.",
                    "search_type": "semantic_search",
                    "matches": 0
                }

            # Format results
            formatted_results = self._format_search_results(results, source)

            return {
                "success": True,
                "source_name": source.get("name", "Unknown"),
                "source_id": source_id,
                "content": formatted_results,
                "search_type": "semantic_search",
                "matches": len(results)
            }

        except ValueError as e:
            # API key not configured
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }

    def _format_search_results(
        self,
        results: list,
        source: Dict[str, Any]
    ) -> str:
        """
        Format Pinecone search results into readable text.

        Educational Note: We format the results in a way that's
        easy for the AI to parse and cite. Each result includes:
        - Page number (from metadata)
        - Relevance score
        - The actual text content

        Args:
            results: List of Pinecone search results
            source: Source metadata

        Returns:
            Formatted string with all matching chunks
        """
        lines = [
            f"## Search Results from: {source.get('name', 'Unknown')}",
            f"Found {len(results)} relevant sections:",
            ""
        ]

        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            metadata = result.get("metadata", {})

            # Metadata uses "page_number" key (from chunking_service)
            page = metadata.get("page_number", "?")
            text = metadata.get("text", "")

            lines.append(f"### Result {i} (Page {page}, Score: {score:.2f})")
            lines.append("")
            lines.append(text)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# Singleton instance
source_search_executor = SourceSearchExecutor()
