"""
Tavily Service - Web search and content extraction using Tavily AI API.

Educational Note: Tavily is an AI-powered search API that provides:
- High-quality search results with AI-generated answers
- Content extraction from specific URLs
- Topic-based filtering (general, news, finance)
- Domain filtering for focused research

Features:
    - search(): Basic search with fixed params
    - search_advanced(): Full-featured search with all options
    - extract(): Extract content from specific URLs
"""

import os
from typing import Dict, Any, List, Optional
from tavily import TavilyClient


class TavilyService:
    """
    Service class for Tavily AI web search.

    Educational Note: We lazy-load the client to avoid errors
    if the API key isn't configured.
    """

    def __init__(self):
        """Initialize the Tavily service."""
        self._client = None

    def _get_client(self) -> TavilyClient:
        """
        Get or create the Tavily client.

        Returns:
            TavilyClient instance

        Raises:
            ValueError: If TAVILY_API_KEY is not configured
        """
        if self._client is None:
            api_key = os.getenv('TAVILY_API_KEY')
            if not api_key:
                raise ValueError(
                    "TAVILY_API_KEY not found in environment. "
                    "Please configure it in App Settings."
                )
            self._client = TavilyClient(api_key=api_key)

        return self._client

    def search(self, query: str) -> Dict[str, Any]:
        """
        Execute a web search using Tavily with optimized defaults.

        Educational Note: Uses fixed parameters for consistent results:
        - include_answer: "advanced" for AI summary
        - search_depth: "advanced" for better results
        - max_results: 5 for good coverage

        Args:
            query: The search query (URL or topic)

        Returns:
            Dict with search results in standardized format
        """
        try:
            client = self._get_client()

            print(f"Tavily search: {query[:50]}...")

            # Execute search with optimized fixed params
            response = client.search(
                query=query,
                include_answer="advanced",
                search_depth="advanced",
                max_results=10,
                chunks_per_source=5
            )

            # Return clean standardized format
            return {
                "success": True,
                "query": response.get("query", query),
                "answer": response.get("answer"),
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")
                    }
                    for r in response.get("results", [])
                ]
            }

        except ValueError as e:
            # API key not configured
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            print(f"Tavily search error: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }

    def search_advanced(
        self,
        operation_type: str,
        query: Optional[str] = None,
        urls: Optional[List[str]] = None,
        topic: str = "general",
        search_depth: str = "advanced",
        max_results: int = 5,
        include_raw_content: bool = True,
        chunks_per_source: int = 3,
        include_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Advanced Tavily operation - supports both search and extract.

        Educational Note: This unified function handles both:
        - search: Query-based web search with topic filtering
        - extract: Direct content extraction from specific URLs

        Returns full results so research agent can cite URLs properly.

        Args:
            operation_type: 'search' or 'extract'
            query: Search query (required for search)
            urls: List of URLs (required for extract)
            topic: Topic filter - 'general', 'news', or 'finance'
            search_depth: 'basic' or 'advanced'
            max_results: Maximum results (1-12, default 5)
            include_raw_content: Include full page content
            chunks_per_source: Content chunks per source
            include_domains: Limit search to these domains

        Returns:
            Dict with full results including URLs for citation
        """
        try:
            client = self._get_client()

            if operation_type == "extract":
                return self._execute_extract(
                    client=client,
                    urls=urls or [],
                    search_depth=search_depth
                )
            else:
                return self._execute_search(
                    client=client,
                    query=query or "",
                    topic=topic,
                    search_depth=search_depth,
                    max_results=min(max_results, 12),
                    include_raw_content=include_raw_content,
                    chunks_per_source=chunks_per_source,
                    include_domains=include_domains
                )

        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            print(f"Tavily advanced error: {e}")
            return {"success": False, "error": f"Operation failed: {str(e)}"}

    def _execute_search(
        self,
        client: TavilyClient,
        query: str,
        topic: str,
        search_depth: str,
        max_results: int,
        include_raw_content: bool,
        chunks_per_source: int,
        include_domains: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Execute advanced web search.

        Educational Note: Returns full results with all fields so the
        research agent has complete context for citations.
        """
        if not query:
            return {"success": False, "error": "Query is required for search"}

        print(f"Tavily advanced search: {query[:50]}... (topic: {topic})")

        # Build search params
        search_params = {
            "query": query,
            "include_answer": "advanced",
            "topic": topic,
            "search_depth": search_depth,
            "max_results": max_results,
            "chunks_per_source": chunks_per_source
        }

        # Add raw content if requested
        if include_raw_content:
            search_params["include_raw_content"] = "text"

        # Add domain filter if provided
        if include_domains:
            search_params["include_domains"] = include_domains

        response = client.search(**search_params)

        # Return full results with all fields for citation context
        results = []
        for r in response.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "raw_content": r.get("raw_content", ""),
                "score": r.get("score", 0)
            })

        return {
            "success": True,
            "type": "search",
            "query": response.get("query", query),
            "answer": response.get("answer"),
            "results": results,
            "result_count": len(results)
        }

    def _execute_extract(
        self,
        client: TavilyClient,
        urls: List[str],
        search_depth: str
    ) -> Dict[str, Any]:
        """
        Execute URL content extraction.

        Educational Note: Extracts content from specific URLs for analysis.
        Returns full results with URL, title, and raw_content for citations.
        """
        if not urls:
            return {"success": False, "error": "URLs are required for extract"}

        print(f"Tavily extract: {len(urls)} URLs (depth: {search_depth})")

        response = client.extract(
            urls=urls,
            extract_depth=search_depth,
            format="text"
        )

        # Return full extracted content with all fields
        results = []
        for r in response.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "raw_content": r.get("raw_content", "")
            })

        # Track failed URLs
        failed_urls = response.get("failed_results", [])

        return {
            "success": True,
            "type": "extract",
            "results": results,
            "result_count": len(results),
            "failed_urls": failed_urls
        }

    def is_configured(self) -> bool:
        """
        Check if Tavily API key is configured.

        Returns:
            True if API key is set, False otherwise
        """
        return bool(os.getenv('TAVILY_API_KEY'))


# Singleton instance
tavily_service = TavilyService()
