"""
Tavily API key validator.

Educational Note: Validates Tavily API keys by making a minimal
search request. Tavily is a search API optimized for LLMs and RAG.
"""
from typing import Tuple
from tavily import TavilyClient


def validate_tavily_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Tavily API key by making a test search request.

    Educational Note: Tavily is a search API optimized for LLMs and RAG.
    We make a simple search request to verify the key works.

    Args:
        api_key: The Tavily API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or api_key == '':
        return False, "API key is empty"

    try:
        # Create Tavily client with the provided key
        tavily_client = TavilyClient(api_key=api_key)

        # Make a simple test search
        response = tavily_client.search("test", max_results=1)

        # If we get a response, the key is valid
        if response:
            return True, "Valid Tavily API key"
        else:
            return False, "API returned empty response"

    except Exception as e:
        error_message = str(e).lower()

        # Check for common error types
        if 'invalid' in error_message or 'unauthorized' in error_message or 'api key' in error_message:
            return False, "Invalid API key"
        elif 'quota' in error_message or 'limit' in error_message:
            return True, "Valid API key (quota exceeded)"
        elif 'rate' in error_message:
            return True, "Valid API key (rate limited)"
        else:
            print(f"Tavily validation error: {type(e).__name__}: {str(e)}")
            return False, f"Validation failed: {str(e)[:100]}"
