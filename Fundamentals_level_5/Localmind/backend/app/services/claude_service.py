"""
Claude Service - Wrapper for Claude API interactions.

Educational Note: This service provides a clean interface to the Claude API.
It's designed to be used by multiple callers (chat, subagents, tools, etc.)
with different configurations (prompts, tools, temperature).

Key Design Decisions:
- Stateless: Each call is independent, caller provides all context
- Flexible: Accepts variable parameters for different use cases
- Reusable: Can be called from main chat, subagents, RAG pipeline, etc.
"""
import os
from typing import Optional, List, Dict, Any
import anthropic

from app.services.cost_tracking_service import cost_tracking_service


class ClaudeService:
    """
    Service class for Claude API interactions.

    Educational Note: This is a thin wrapper around the Anthropic client.
    It handles client initialization and provides a consistent interface
    for making API calls with various configurations.
    """

    def __init__(self):
        """Initialize the Claude service."""
        self._client: Optional[anthropic.Anthropic] = None

    def _get_client(self) -> anthropic.Anthropic:
        """
        Get or create the Anthropic client.

        Educational Note: Lazy initialization to avoid errors if API key
        is not set at import time.

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set
        """
        if self._client is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def send_message(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send messages to Claude and get a response.

        Educational Note: This is the core method for Claude API interaction.
        Different callers can customize behavior via parameters:
        - Main chat: Just messages + system prompt
        - Subagents: Messages + tools + specific prompts
        - RAG: Messages with context + retrieval tools

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt for this conversation
            model: Claude model to use (default: claude-sonnet-4-5-20250929)
            max_tokens: Maximum tokens in response (default: 4096)
            temperature: Sampling temperature (default: 0.2)
            tools: Optional list of tool definitions for tool use
            tool_choice: Optional tool choice configuration
            extra_headers: Optional headers for beta features (e.g., {"anthropic-beta": "web-fetch-2025-09-10"})
            project_id: Optional project ID for cost tracking (if provided, costs are tracked)

        Returns:
            Dict containing:
                - content: The response content (text or tool_use blocks)
                - model: Model used
                - usage: Token usage stats
                - stop_reason: Why the response ended
                - raw_response: Full API response for advanced use cases

        Raises:
            ValueError: If API key is not configured
            anthropic.APIError: If API call fails
        """
        client = self._get_client()

        # Build API call parameters
        api_params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        # Add optional parameters only if provided
        if system_prompt:
            api_params["system"] = system_prompt

        if temperature != 0.2:  # Only set if not default
            api_params["temperature"] = temperature

        if tools:
            api_params["tools"] = tools

        if tool_choice:
            api_params["tool_choice"] = tool_choice

        # Add extra headers for beta features (e.g., web_fetch)
        if extra_headers:
            api_params["extra_headers"] = extra_headers

        # Make API call
        response = client.messages.create(**api_params)

        # Track costs if project_id provided
        if project_id:
            cost_tracking_service.add_usage(
                project_id=project_id,
                model=response.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )

        # Extract and return structured response
        return {
            "content": self._extract_content(response),
            "content_blocks": response.content,  # Raw content blocks for tool use
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
            "raw_response": response,
        }
    

    def _extract_content(self, response: anthropic.types.Message) -> str:
        """
        Extract text content from response.

        Educational Note: Claude responses can have multiple content blocks
        (text, tool_use, etc.). This extracts just the text for simple cases.
        For tool use, callers should use content_blocks directly.

        Args:
            response: The raw API response

        Returns:
            Concatenated text content from all text blocks
        """
        text_parts = []
        for block in response.content:
            # Check both that attribute exists AND is not None
            if hasattr(block, 'text') and block.text is not None:
                text_parts.append(block.text)
        return "".join(text_parts)

    def is_tool_use_response(self, response: Dict[str, Any]) -> bool:
        """
        Check if response contains tool use requests.

        Educational Note: When Claude wants to use a tool, it returns
        tool_use content blocks. The caller needs to execute the tool
        and send back tool_result messages.

        Args:
            response: Response dict from send_message

        Returns:
            True if response contains tool_use blocks
        """
        for block in response.get("content_blocks", []):
            if hasattr(block, 'type') and block.type == "tool_use":
                return True
        return False

    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool call information from response.

        Educational Note: When Claude wants to use tools, we need to
        extract the tool name, ID, and input parameters to execute them.

        Args:
            response: Response dict from send_message

        Returns:
            List of tool call dicts with id, name, and input
        """
        tool_calls = []
        for block in response.get("content_blocks", []):
            if hasattr(block, 'type') and block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return tool_calls

    def count_tokens(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        Count input tokens for a given set of messages without making an API call.

        Educational Note: This is useful for determining context size before:
        - Deciding whether to use RAG vs full context
        - Estimating costs
        - Checking if content fits within model limits

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to include in count
            model: Claude model to use for tokenization
            tools: Optional list of tool definitions (tools also consume tokens)

        Returns:
            Number of input tokens
        """
        client = self._get_client()

        # Build API call parameters
        api_params = {
            "model": model,
            "messages": messages,
        }

        # Add optional parameters
        if system_prompt:
            api_params["system"] = system_prompt

        if tools:
            api_params["tools"] = tools

        # Call the count_tokens API
        response = client.messages.count_tokens(**api_params)

        return response.input_tokens


# Singleton instance for easy import
claude_service = ClaudeService()
