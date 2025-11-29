"""
Tavily Service - Web search using Tavily AI API.

Educational Note: Tavily is an AI-powered search API that provides
high-quality search results with optional AI-generated answers.
We use it as a fallback when Claude's web_fetch fails, or for
comprehensive web searches.

API Endpoints:
    POST /search - Execute a search query

Features:
    - AI-generated answer summarizing results
    - Raw content extraction in markdown format
    - Domain filtering (include/exclude)
    - Search depth control (basic/advanced)
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

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_raw_content: bool = True,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a web search using Tavily.

        Educational Note: This method wraps the Tavily search API.
        We return a standardized response format that can be used
        as a tool result in the web agent.

        Args:
            query: The search query (can be a URL or general query)
            search_depth: "basic" or "advanced" (advanced costs more)
            include_answer: Include AI-generated answer
            include_raw_content: Include full page content in markdown
            max_results: Maximum number of results (1-10)
            include_domains: Only search these domains
            exclude_domains: Exclude these domains from results

        Returns:
            Dict with search results in standardized format
        """
        try:
            client = self._get_client()

            # Build search parameters
            search_params = {
                "query": query,
                "search_depth": search_depth,
                "include_answer": include_answer,
                "include_raw_content": "markdown" if include_raw_content else False,
                "max_results": max_results
            }

            # Add domain filters if specified
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains

            print(f"Tavily search: {query[:100]}...")

            # Execute search
            response = client.search(**search_params)

            # Standardize response format
            return {
                "success": True,
                "query": response.get("query", query),
                "answer": response.get("answer"),
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", ""),
                        "raw_content": r.get("raw_content"),
                        "score": r.get("score", 0)
                    }
                    for r in response.get("results", [])
                ],
                "response_time": response.get("response_time")
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
