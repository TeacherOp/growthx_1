"""
Web Agent Service - AI agent for web content extraction and search.

Educational Note: This service implements an agentic loop for web operations.
It uses existing services for consistency:
    - prompt_loader: Load agent system prompt
    - tool_loader: Load server and client tools
    - claude_service: Make API calls
    - message_service: Parse tool calls from responses
    - web_agent_executor: Execute client tools

Agent Loop Flow:
    1. Send task to Claude with available tools
    2. Claude responds with tool calls or text
    3. For server tools: results come automatically in response
    4. For client tools: executor handles, we send results back
    5. Loop until return_search_result is called
    6. Return final extracted content
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import Config
from app.services.integrations.claude import claude_service
from app.config import prompt_loader, tool_loader
from app.services.tool_executors import web_agent_executor


class WebAgentService:
    """
    Service class for web content extraction agent.

    Educational Note: This agent orchestrates web fetching and searching
    using a combination of Claude's server tools and custom tools.
    """

    # Agent name for loading prompts and tools
    AGENT_NAME = "web_agent"

    # Maximum iterations to prevent infinite loops
    MAX_ITERATIONS = 10

    def __init__(self):
        """Initialize the web agent service."""
        self._tools_cache = None

    def _get_tools(self) -> Dict[str, Any]:
        """
        Load tools using tool_loader.

        Returns:
            Dict with 'server_tools', 'client_tools', 'all_tools', 'beta_headers'
        """
        if self._tools_cache is None:
            self._tools_cache = tool_loader.load_tools_for_agent(self.AGENT_NAME)
            # Combine for API calls (server tools + client tools)
            self._tools_cache["all_tools"] = (
                self._tools_cache["server_tools"] +
                self._tools_cache["client_tools"]
            )
        return self._tools_cache

    def _get_system_prompt(self) -> str:
        """
        Load system prompt using prompt_loader.

        Returns:
            System prompt string
        """
        prompt = prompt_loader.get_agent_prompt(self.AGENT_NAME)
        if not prompt:
            # Fallback prompt
            prompt = (
                "You are a web content extraction agent. "
                "Extract content from URLs using available tools. "
                "Always call return_search_result when done."
            )
        return prompt

    def extract_from_url(
        self,
        url: str,
        project_id: Optional[str] = None,
        source_id: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract content from a URL using the web agent.

        Educational Note: This is the main entry point for URL extraction.
        The agent will:
        1. Try web_fetch first
        2. Fall back to tavily_search if web_fetch fails
        3. Return structured content via return_search_result

        Args:
            url: The URL to extract content from
            project_id: Optional project ID for saving execution logs
            source_id: Optional source ID for reference in logs
            additional_context: Optional context about what to extract

        Returns:
            Dict with extracted content and metadata
        """
        task = f"Extract all content from this URL: {url}"
        if additional_context:
            task += f"\n\nAdditional context: {additional_context}"

        return self._run_agent(task, project_id=project_id, source_id=source_id, url=url)

    def search_web(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search the web using the agent.

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            Dict with search results and synthesized content
        """
        task = f"Search the web for: {query}\n\nReturn the top {max_results} most relevant results with their content."
        return self._run_agent(task)

    def _run_agent(
        self,
        task: str,
        project_id: Optional[str] = None,
        source_id: Optional[str] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the agent loop with a task.

        Educational Note: This implements the agentic loop using existing services:
        - claude_service for API calls
        - message_service for parsing tool calls
        - web_agent_executor for executing client tools

        Args:
            task: The task description for the agent
            project_id: Optional project ID for saving execution logs
            source_id: Optional source ID for reference
            url: Optional URL being processed

        Returns:
            Dict with agent result
        """
        # Generate execution ID for logging
        execution_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        system_prompt = self._get_system_prompt()
        tools_config = self._get_tools()
        all_tools = tools_config["all_tools"]

        # Build extra_headers for beta features (e.g., web_fetch)
        extra_headers = None
        beta_headers = tools_config.get("beta_headers", [])
        # Filter out None values before joining
        valid_beta_headers = [h for h in beta_headers if h is not None]
        if valid_beta_headers:
            extra_headers = {"anthropic-beta": ",".join(valid_beta_headers)}

        # Initialize conversation
        messages = [{"role": "user", "content": task}]

        # Track usage
        total_input_tokens = 0
        total_output_tokens = 0
        iteration = 0

        print(f"Web Agent starting: {task[:100]}...")

        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            print(f"  Iteration {iteration}/{self.MAX_ITERATIONS}")

            # Call Claude using claude_service
            response = claude_service.send_message(
                messages=messages,
                system_prompt=system_prompt,
                tools=all_tools,
                max_tokens=8192,
                temperature=0,
                extra_headers=extra_headers,
                project_id=project_id
            )

            # Track usage
            total_input_tokens += response["usage"]["input_tokens"]
            total_output_tokens += response["usage"]["output_tokens"]

            # Process response
            result = self._process_response(response, messages)

            if result["done"]:
                # Agent completed
                final_result = result.get("final_result", {})
                print(f"  Agent completed in {iteration} iterations")
                agent_result = {
                    "success": final_result.get("success", False),
                    "title": final_result.get("title", ""),
                    "url": final_result.get("url", ""),
                    "content": final_result.get("content", ""),
                    "summary": final_result.get("summary", ""),
                    "content_type": final_result.get("content_type", "other"),
                    "source_urls": final_result.get("source_urls", []),
                    "error_message": final_result.get("error_message"),
                    "iterations": iteration,
                    "usage": {
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens
                    },
                    "extracted_at": datetime.now().isoformat()
                }
                # Save execution log
                self._save_execution(
                    project_id=project_id,
                    execution_id=execution_id,
                    source_id=source_id,
                    url=url,
                    task=task,
                    messages=messages,
                    result=agent_result,
                    started_at=started_at
                )
                return agent_result

            if result["end_turn"]:
                # Agent ended without calling termination tool
                print(f"  Agent ended without explicit result")
                agent_result = {
                    "success": False,
                    "error_message": "Agent ended without returning a result",
                    "content": response.get("content", ""),
                    "iterations": iteration,
                    "usage": {
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens
                    }
                }
                # Save execution log
                self._save_execution(
                    project_id=project_id,
                    execution_id=execution_id,
                    source_id=source_id,
                    url=url,
                    task=task,
                    messages=messages,
                    result=agent_result,
                    started_at=started_at
                )
                return agent_result

        # Max iterations reached
        print(f"  Agent reached max iterations ({self.MAX_ITERATIONS})")
        agent_result = {
            "success": False,
            "error_message": f"Agent reached maximum iterations ({self.MAX_ITERATIONS})",
            "iterations": iteration,
            "usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens
            }
        }
        # Save execution log
        self._save_execution(
            project_id=project_id,
            execution_id=execution_id,
            source_id=source_id,
            url=url,
            task=task,
            messages=messages,
            result=agent_result,
            started_at=started_at
        )
        return agent_result

    def _process_response(
        self,
        response: Dict[str, Any],
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process Claude's response and handle tool calls.

        Educational Note: This method:
        1. Extracts tool calls using message_service
        2. Executes client tools using web_agent_executor
        3. Updates messages for next iteration
        4. Detects termination signal

        Args:
            response: Response from claude_service
            messages: Conversation messages (mutated in place)

        Returns:
            Dict with 'done', 'end_turn', and optionally 'final_result'
        """
        content_blocks = response.get("content_blocks", [])
        stop_reason = response.get("stop_reason")

        # Build assistant content for message history
        assistant_content = []
        tool_results_to_send = []
        final_result = None

        for block in content_blocks:
            block_type = getattr(block, "type", None)

            if block_type == "text":
                text_content = getattr(block, "text", "")
                assistant_content.append({"type": "text", "text": text_content})
                if text_content:
                    print(f"    Agent: {text_content[:100]}...")

            elif block_type == "tool_use":
                # Client tool - we need to execute
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                print(f"    Tool call: {tool_name}")

                # Add tool_use to assistant content
                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_id,
                    "name": tool_name,
                    "input": tool_input
                })

                # Execute using web_agent_executor
                result, is_termination = web_agent_executor.execute_tool(
                    tool_name, tool_input
                )

                if is_termination:
                    final_result = result
                    tool_results_to_send.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps({"status": "completed"})
                    })
                else:
                    tool_results_to_send.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result)
                    })

            elif block_type == "server_tool_use":
                # Server tool - Claude handles execution
                assistant_content.append({
                    "type": "server_tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                print(f"    Server tool: {block.name}")

            elif block_type == "web_search_tool_result":
                # Server tool results - include in assistant content
                assistant_content.append({
                    "type": "web_search_tool_result",
                    "tool_use_id": getattr(block, "tool_use_id", None),
                    "content": getattr(block, "content", None)
                })

            elif block_type == "web_fetch_tool_result":
                # Server tool results - include in assistant content
                assistant_content.append({
                    "type": "web_fetch_tool_result",
                    "tool_use_id": getattr(block, "tool_use_id", None),
                    "content": getattr(block, "content", None)
                })

        # Check if we have a final result
        if final_result is not None:
            return {"done": True, "final_result": final_result, "end_turn": False}

        # Check if agent ended without tools
        if stop_reason == "end_turn" and not tool_results_to_send:
            return {"done": False, "end_turn": True}

        # Continue conversation if there are tool results
        if tool_results_to_send:
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results_to_send})
        elif stop_reason == "tool_use":
            # Tool use but no client tools (server tools only)
            messages.append({"role": "assistant", "content": assistant_content})

        return {"done": False, "end_turn": False}

    def _save_execution(
        self,
        project_id: Optional[str],
        execution_id: str,
        source_id: Optional[str],
        url: Optional[str],
        task: str,
        messages: List[Dict[str, Any]],
        result: Dict[str, Any],
        started_at: str
    ) -> None:
        """
        Save the agent execution log to a JSON file.

        Educational Note: Saving execution logs enables:
        - Debugging agent behavior
        - Analyzing tool usage patterns
        - Auditing content extraction quality

        Structure:
            data/projects/{project_id}/agents/web_agent/{execution_id}.json

        Args:
            project_id: Project ID (if None, logs are not saved)
            execution_id: Unique execution ID
            source_id: Source ID being processed
            url: URL being extracted
            task: The task description
            messages: Full message chain
            result: Agent result
            started_at: Execution start timestamp
        """
        if not project_id:
            print("  No project_id provided, skipping execution log save")
            return

        try:
            # Build directory path
            agents_dir = Path(Config.DATA_DIR) / "projects" / project_id / "agents" / "web_agent"
            agents_dir.mkdir(parents=True, exist_ok=True)

            # Build execution log
            execution_log = {
                "execution_id": execution_id,
                "agent_name": self.AGENT_NAME,
                "source_id": source_id,
                "url": url,
                "task": task,
                "messages": messages,
                "result": result,
                "started_at": started_at,
                "completed_at": datetime.now().isoformat()
            }

            # Save to file
            log_file = agents_dir / f"{execution_id}.json"
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(execution_log, f, indent=2, ensure_ascii=False)

            print(f"  Execution log saved: {log_file}")

        except Exception as e:
            print(f"  Error saving execution log: {e}")


# Singleton instance
web_agent_service = WebAgentService()
