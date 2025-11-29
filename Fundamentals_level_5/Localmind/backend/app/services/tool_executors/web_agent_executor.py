"""
Web Agent Executor - Handles tool execution for the web agent.

Educational Note: This executor routes tool calls from the web agent
to the appropriate services. It handles:
    - tavily_search: Routes to tavily_service
    - return_search_result: Extracts final result (termination signal)

Server tools (web_search, web_fetch) are handled by Claude automatically
and don't need execution here.
"""

from typing import Dict, Any, Tuple, Union


class WebAgentExecutor:
    """
    Executor for web agent tools.

    Educational Note: The executor pattern separates tool routing from
    the agent loop logic. This makes it easy to add new tools or
    modify execution behavior without changing the agent service.
    """

    # Tool that signals agent completion
    TERMINATION_TOOL = "return_search_result"

    def __init__(self):
        """Initialize the executor."""
        pass

    def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Execute a tool and return the result.

        Educational Note: Returns a tuple of (result, is_termination).
        The is_termination flag tells the agent loop to stop processing.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tuple of (tool_result, is_termination_signal)
        """
        # Check for termination tool
        if tool_name == self.TERMINATION_TOOL:
            return self._handle_termination(tool_input), True

        # Route to appropriate service
        if tool_name == "tavily_search":
            result = self._execute_tavily_search(tool_input)
            return result, False

        # Unknown tool
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }, False

    def _execute_tavily_search(self, tool_input: Dict[str, Any]) -> str:
        """
        Execute Tavily search tool and format result as readable string.

        Args:
            tool_input: Contains 'query' parameter

        Returns:
            Formatted search results as a string for Claude to use
        """
        from app.services.integrations.tavily import tavily_service

        query = tool_input.get("query", "")
        result = tavily_service.search(query=query)

        # Format the result as a clean readable string
        if not result.get("success"):
            return f"Search failed: {result.get('error', 'Unknown error')}"

        # Build formatted output
        output_parts = []

        # Add AI-generated answer if available
        answer = result.get("answer")
        if answer:
            output_parts.append(f"## Summary\n{answer}")

        # Add search results
        results = result.get("results", [])
        if results:
            output_parts.append("\n## Sources")
            for i, r in enumerate(results, 1):
                title = r.get("title", "Untitled")
                url = r.get("url", "")
                content = r.get("content", "")
                output_parts.append(f"\n### {i}. {title}\nURL: {url}\n{content}")

        return "\n".join(output_parts) if output_parts else "No results found."

    def _handle_termination(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the termination tool (return_search_result).

        Educational Note: This tool signals that the agent has finished
        its task. We extract and validate the final result structure.

        Args:
            tool_input: Final result from the agent

        Returns:
            Validated result structure
        """
        # Validate required fields
        success = tool_input.get("success", False)
        content = tool_input.get("content", "")

        if not content and success:
            return {
                "success": False,
                "error": "No content provided despite success=true"
            }

        # Return the structured result
        return {
            "success": success,
            "title": tool_input.get("title", ""),
            "url": tool_input.get("url", ""),
            "content": content,
            "summary": tool_input.get("summary", ""),
            "content_type": tool_input.get("content_type", "other"),
            "source_urls": tool_input.get("source_urls", []),
            "error_message": tool_input.get("error_message")
        }

    def is_termination_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is the termination signal.

        Args:
            tool_name: Name of the tool

        Returns:
            True if this tool signals agent completion
        """
        return tool_name == self.TERMINATION_TOOL


# Singleton instance
web_agent_executor = WebAgentExecutor()
