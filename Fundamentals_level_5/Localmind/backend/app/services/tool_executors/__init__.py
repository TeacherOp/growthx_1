"""
Tool Executors - Handle tool call execution for AI services.

Educational Note: This folder contains executors that handle tool calls
from Claude during chat or agent loops. Each executor is responsible for:
- Receiving tool call parameters
- Executing the appropriate action
- Returning results back to the AI

Executors:
- memory_executor: Handles store_memory tool calls (non-blocking, background task)
- source_search_executor: Handles search_sources tool calls (full content or semantic search)
- web_agent_executor: Routes tool calls for web agent (tavily_search, return_search_result)
- deep_research_executor: Routes tool calls for deep research (write_research_to_file, tavily_search_advance)
"""
from app.services.tool_executors.memory_executor import memory_executor
from app.services.tool_executors.source_search_executor import source_search_executor
from app.services.tool_executors.web_agent_executor import web_agent_executor
from app.services.tool_executors.deep_research_executor import deep_research_executor

__all__ = ["memory_executor", "source_search_executor", "web_agent_executor", "deep_research_executor"]
