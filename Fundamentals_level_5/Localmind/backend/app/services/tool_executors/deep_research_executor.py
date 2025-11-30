"""
Deep Research Executor - Handles tool execution for the deep research agent.

Educational Note: This executor routes tool calls from the deep research agent
to the appropriate services. It handles:
    - write_research_to_file: Writes research segments to output file
    - tavily_search_advance: Routes to tavily_service for search/extract

Server tools (web_search) are handled by Claude automatically.
Termination is signaled when write_research_to_file has is_last_segment=true.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple


class DeepResearchExecutor:
    """
    Executor for deep research agent tools.

    Educational Note: The executor pattern separates tool routing from
    the agent loop logic. This makes it easy to add new tools or
    modify execution behavior without changing the agent service.
    """

    # Tool that can signal agent completion (when is_last_segment=true)
    WRITE_TOOL = "write_research_to_file"

    def __init__(self):
        """Initialize the executor."""
        pass

    def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        output_path: str = None
    ) -> Tuple[str, bool]:
        """
        Execute a tool and return the result.

        Educational Note: Returns a tuple of (result_message, is_termination).
        The is_termination flag tells the agent loop to stop processing.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            output_path: Path for write_research_to_file output

        Returns:
            Tuple of (tool_result_message, is_termination_signal)
        """
        if tool_name == self.WRITE_TOOL:
            return self._execute_write_research(tool_input, output_path)

        if tool_name == "tavily_search_advance":
            result = self._execute_tavily_search(tool_input)
            return result, False

        # Unknown tool
        return f"Unknown tool: {tool_name}", False

    def _execute_write_research(
        self,
        tool_input: Dict[str, Any],
        output_path: str
    ) -> Tuple[str, bool]:
        """
        Execute write_research_to_file tool.

        Educational Note: Writes research segments incrementally to file.
        Returns (result_message, is_termination) - termination is true
        when is_last_segment=true.

        Args:
            tool_input: Contains segment_number, operation, is_last_segment, research_content
            output_path: Path to write the research output

        Returns:
            Tuple of (message for agent, should_terminate)
        """
        operation = tool_input.get("operation", "write")
        content = tool_input.get("research_content", "")
        segment_number = tool_input.get("segment_number", 1)
        is_last_segment = tool_input.get("is_last_segment", False)

        if not output_path:
            return "Error: No output path provided for writing research.", False

        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            if operation == "write":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"      [Executor] Wrote segment {segment_number} to file")
            else:
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n\n" + content)
                print(f"      [Executor] Appended segment {segment_number} to file")

            if is_last_segment:
                return "Research document completed and saved successfully.", True
            else:
                return f"Segment {segment_number} written successfully. Continue your research and write more segments.", False

        except Exception as e:
            print(f"      [Executor] Error writing segment: {e}")
            return f"Error writing segment: {str(e)}", False

    def _execute_tavily_search(self, tool_input: Dict[str, Any]) -> str:
        """
        Execute tavily_search_advance tool.

        Educational Note: Delegates to tavily_service.search_advanced()
        which handles both 'search' and 'extract' operations.

        Args:
            tool_input: Contains type, query/urls, and search options

        Returns:
            Formatted search results as JSON string
        """
        from app.services.integrations.tavily import tavily_service

        operation_type = tool_input.get("type", "search")

        result = tavily_service.search_advanced(
            operation_type=operation_type,
            query=tool_input.get("query"),
            urls=tool_input.get("urls"),
            topic=tool_input.get("topic", "general"),
            search_depth=tool_input.get("search_depth", "advanced"),
            max_results=tool_input.get("max_results", 5),
            include_raw_content=tool_input.get("include_raw_content", True),
            chunks_per_source=tool_input.get("chunks_per_source", 3),
            include_domains=tool_input.get("include_domains")
        )

        return json.dumps(result)

    def is_termination_result(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """
        Check if a tool call signals termination.

        Educational Note: For deep research, termination happens when
        write_research_to_file is called with is_last_segment=true.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            True if this tool call signals agent completion
        """
        if tool_name == self.WRITE_TOOL:
            return tool_input.get("is_last_segment", False)
        return False


# Singleton instance
deep_research_executor = DeepResearchExecutor()
