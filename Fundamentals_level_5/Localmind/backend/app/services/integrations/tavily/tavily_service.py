"""
Tavily Service - Web search using Tavily AI API.

Educational Note: Tavily is an AI-powered search API that provides
high-quality search results with optional AI-generated answers.
We use it as a fallback when Claude's web_fetch fails.

Features:
    - AI-generated answer summarizing results
    - Search depth control (basic/advanced)
"""

import os
from typing import Dict, Any
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

    def is_configured(self) -> bool:
        """
        Check if Tavily API key is configured.

        Returns:
            True if API key is set, False otherwise
        """
        return bool(os.getenv('TAVILY_API_KEY'))


# Singleton instance
tavily_service = TavilyService()
