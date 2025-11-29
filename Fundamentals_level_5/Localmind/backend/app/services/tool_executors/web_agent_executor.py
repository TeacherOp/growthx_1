"""
Web Agent Executor - Handles tool execution for the web agent.

Educational Note: This executor routes tool calls from the web agent
to the appropriate services. It handles:
    - tavily_search: Routes to tavily_service
    - return_search_result: Extracts final result (termination signal)

Server tools (web_search, web_fetch) are handled by Claude automatically
and don't need execution here.
"""

from typing import Dict, Any, Optional, Tuple


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

    def _execute_tavily_search(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Tavily search tool.

        Args:
            tool_input: Search parameters from the agent

        Returns:
            Search results in standardized format
        """
        from app.services.integrations.tavily import tavily_service

        return tavily_service.search(
            query=tool_input.get("query", ""),
            search_depth=tool_input.get("search_depth", "basic"),
            include_answer=tool_input.get("include_answer", True),
            include_raw_content=tool_input.get("include_raw_content", True),
            max_results=tool_input.get("max_results", 5),
            include_domains=tool_input.get("include_domains")
        )

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
