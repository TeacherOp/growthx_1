"""
Main Chat Service - Orchestrates chat message processing and AI responses.

Educational Note: This service handles the core chat logic with tool support.

Message Flow:
1. User message - What the user types in chat
2. Assistant response - Two types:
   a. Text response - Final answer to user (stored and displayed)
   b. Tool use - Claude wants to search sources
3. User message (tool_result) - Results from tool execution sent back
4. Repeat 2-3 until Claude gives text response

The service uses message_service for all message handling and tool parsing.

Debug Logging:
Each API call to Claude is logged to:
    data/projects/{project_id}/chats/{chat_id}/api_1.json, api_2.json, etc.
This helps debug complex tool chains and message construction.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from config import Config
from app.services.data_services import chat_service
from app.services.integrations.claude import claude_service
from app.services.data_services import message_service
from app.config import prompt_loader, tool_loader, context_loader
from app.services.tool_executors import source_search_executor
from app.services.tool_executors import memory_executor
from app.services.tool_executors import csv_analyzer_agent_executor
from app.services.ai_services import chat_naming_service
from app.services.background_services import task_service
from app.utils import claude_parsing_utils


class MainChatService:
    """
    Service class for orchestrating chat conversations with tool support.

    Educational Note: This service coordinates the message flow between
    user, Claude, and tools. It uses message_service for all message
    operations and tool parsing.
    """

    # Maximum tool iterations to prevent infinite loops
    MAX_TOOL_ITERATIONS = 10

    def __init__(self):
        """Initialize the service."""
        self._search_tool = None
        self._memory_tool = None
        self._csv_analyzer_tool = None
        self.projects_dir = Config.PROJECTS_DIR

    def _get_search_tool(self) -> Dict[str, Any]:
        """Load the search_sources tool definition (cached)."""
        if self._search_tool is None:
            self._search_tool = tool_loader.load_tool("chat_tools", "source_search_tool")
        return self._search_tool

    def _get_memory_tool(self) -> Dict[str, Any]:
        """Load the store_memory tool definition (cached)."""
        if self._memory_tool is None:
            self._memory_tool = tool_loader.load_tool("chat_tools", "memory_tool")
        return self._memory_tool

    def _get_csv_analyzer_tool(self) -> Dict[str, Any]:
        """Load the analyze_csv_agent tool definition (cached)."""
        if self._csv_analyzer_tool is None:
            self._csv_analyzer_tool = tool_loader.load_tool("chat_tools", "analyze_csv_agent_tool")
        return self._csv_analyzer_tool

    def _get_tools(self, has_active_sources: bool, has_csv_sources: bool = False) -> List[Dict[str, Any]]:
        """
        Get tools list for Claude API call.

        Educational Note: Memory tool is always available. Search tool
        is only available when there are active non-CSV sources. CSV analyzer
        tool is available when there are CSV sources.

        Args:
            has_active_sources: Whether project has active non-CSV sources
            has_csv_sources: Whether project has active CSV sources

        Returns:
            List of tool definitions
        """
        tools = [self._get_memory_tool()]  # Always include memory tool

        if has_active_sources:
            tools.append(self._get_search_tool())

        if has_csv_sources:
            tools.append(self._get_csv_analyzer_tool())

        return tools

    # =========================================================================
    # Debug Logging
    # =========================================================================

    def _get_chat_logs_dir(self, project_id: str, chat_id: str) -> Path:
        """Get the debug logs directory for a chat."""
        logs_dir = self.projects_dir / project_id / "chats" / chat_id
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    def _get_next_api_call_number(self, logs_dir: Path) -> int:
        """
        Get the next API call number for logging.

        Educational Note: We look at existing api_*.json files and
        increment to get the next number.
        """
        existing = list(logs_dir.glob("api_*.json"))
        if not existing:
            return 1

        # Extract numbers from filenames
        numbers = []
        for f in existing:
            try:
                num = int(f.stem.replace("api_", ""))
                numbers.append(num)
            except ValueError:
                continue

        return max(numbers) + 1 if numbers else 1

    def _log_api_call(
        self,
        project_id: str,
        chat_id: str,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        model: str,
        max_tokens: int,
        temperature: float,
        response: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an API call to Claude for debugging.

        Educational Note: This creates a JSON file with the complete
        request and response for each API call. Helps debug:
        - System prompt construction
        - Message chain building
        - Tool definitions
        - Response parsing
        """
        logs_dir = self._get_chat_logs_dir(project_id, chat_id)
        call_number = self._get_next_api_call_number(logs_dir)

        log_data = {
            "call_number": call_number,
            "timestamp": datetime.now().isoformat(),
            "request": {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system_prompt": system_prompt,
                "tools": tools,
                "messages": messages
            }
        }

        # Add response if available
        if response:
            log_data["response"] = {
                "stop_reason": response.get("stop_reason"),
                "model": response.get("model"),
                "usage": response.get("usage"),
                "content": response.get("content"),
                # Serialize content_blocks for readability
                "content_blocks": claude_parsing_utils.serialize_content_blocks(
                    response.get("content_blocks", [])
                )
            }

        log_file = logs_dir / f"api_{call_number}.json"

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"Logged API call {call_number} to: {log_file}")

    def _build_system_prompt(self, project_id: str, base_prompt: str) -> str:
        """
        Build system prompt with memory and source context appended.

        Educational Note: Context is rebuilt on every message to reflect
        current state (memory updates, active/inactive sources).
        Includes both memory context (personalization) and source context (tools).
        """
        full_context = context_loader.build_full_context(project_id)
        if full_context:
            return base_prompt + "\n" + full_context
        return base_prompt

    def _execute_tool(self, project_id: str, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool and return result string.

        Educational Note: Routes tool calls to appropriate executor.
        - search_sources: Searches project sources for information
        - store_memory: Stores user/project memory (non-blocking, queues background task)
        - analyze_csv_agent: Triggers CSV analyzer agent for CSV data questions
        """
        if tool_name == "search_sources":
            result = source_search_executor.execute(
                project_id=project_id,
                source_id=tool_input.get("source_id", ""),
                keywords=tool_input.get("keywords"),
                query=tool_input.get("query")
            )
            if result.get("success"):
                return result.get("content", "No content found")
            else:
                return f"Error: {result.get('error', 'Unknown error')}"

        elif tool_name == "store_memory":
            # Memory tool returns immediately, actual update happens in background
            result = memory_executor.execute(
                project_id=project_id,
                user_memory=tool_input.get("user_memory"),
                project_memory=tool_input.get("project_memory"),
                why_generated=tool_input.get("why_generated", "")
            )
            if result.get("success"):
                return result.get("message", "Memory stored successfully")
            else:
                return f"Error: {result.get('message', 'Unknown error')}"

        elif tool_name == "analyze_csv_agent":
            # CSV analyzer agent for answering questions about CSV data
            result = csv_analyzer_agent_executor.execute(
                project_id=project_id,
                source_id=tool_input.get("source_id", ""),
                query=tool_input.get("query", "")
            )
            if result.get("success"):
                content = result.get("content", "No analysis result")
                # Include image filenames if any plots were generated
                # Educational Note: Filenames are auto-generated unique IDs
                # Main chat Claude MUST use these exact filenames with [[image:FILENAME]]
                if result.get("image_paths"):
                    content += f"\n\nGenerated visualizations (use these exact filenames):\n"
                    for filename in result["image_paths"]:
                        content += f"- [[image:{filename}]]\n"
                return content
            else:
                return f"Error: {result.get('error', 'Analysis failed')}"

        else:
            return f"Unknown tool: {tool_name}"

    def send_message(
        self,
        project_id: str,
        chat_id: str,
        user_message_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process a user message and get AI response.

        Educational Note: This method handles the complete message flow:
        1. Store user message
        2. Build context and call Claude
        3. If tool_use: execute tool, send result, call again
        4. When text response: store and return

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            user_message_text: The user's message text

        Returns:
            Tuple of (user_message_dict, assistant_message_dict)
        """
        # Verify chat exists
        chat = chat_service.get_chat(project_id, chat_id)
        if not chat:
            raise ValueError("Chat not found")

        # Step 1: Store user message
        user_msg = message_service.add_user_message(project_id, chat_id, user_message_text)

        # Step 2: Get config and build system prompt
        prompt_config = prompt_loader.get_project_prompt_config(project_id)
        base_prompt = prompt_config.get("system_prompt", "")
        system_prompt = self._build_system_prompt(project_id, base_prompt)

        # Step 3: Get tools (memory always available, search for non-CSV, analyzer for CSV)
        active_sources = context_loader.get_active_sources(project_id)
        # Separate CSV sources from other sources
        csv_sources = [s for s in active_sources if s.get("file_extension") == ".csv"]
        non_csv_sources = [s for s in active_sources if s.get("file_extension") != ".csv"]
        tools = self._get_tools(
            has_active_sources=bool(non_csv_sources),
            has_csv_sources=bool(csv_sources)
        )

        try:
            # Step 4: Build messages and call Claude
            api_messages = message_service.build_api_messages(project_id, chat_id)

            response = claude_service.send_message(
                messages=api_messages,
                system_prompt=system_prompt,
                model=prompt_config.get("model"),
                max_tokens=prompt_config.get("max_tokens"),
                temperature=prompt_config.get("temperature"),
                tools=tools,
                project_id=project_id
            )

            # Log the API call for debugging
            self._log_api_call(
                project_id=project_id,
                chat_id=chat_id,
                system_prompt=system_prompt,
                messages=api_messages,
                tools=tools,
                model=prompt_config.get("model"),
                max_tokens=prompt_config.get("max_tokens"),
                temperature=prompt_config.get("temperature"),
                response=response
            )

            # Step 5: Handle tool use loop
            # Educational Note: When Claude wants to use tools, stop_reason is "tool_use".
            # We must execute tools and send back tool_result for each tool_use block.
            iteration = 0
            while claude_parsing_utils.is_tool_use(response) and iteration < self.MAX_TOOL_ITERATIONS:
                iteration += 1

                # Get tool_use blocks from response (can be multiple for parallel tool calls)
                tool_use_blocks = claude_parsing_utils.extract_tool_use_blocks(response)

                if not tool_use_blocks:
                    break

                # First, store the assistant's tool_use response
                # Educational Note: The message chain must be:
                # user -> assistant (tool_use[]) -> user (tool_result[]) -> assistant
                # We must store the tool_use response before the tool_result
                serialized_content = claude_parsing_utils.serialize_content_blocks(
                    response.get("content_blocks", [])
                )
                message_service.add_message(
                    project_id=project_id,
                    chat_id=chat_id,
                    role="assistant",
                    content=serialized_content
                )

                # Execute each tool and add results
                for tool_block in tool_use_blocks:
                    tool_id = tool_block.get("id")
                    tool_name = tool_block.get("name")
                    tool_input = tool_block.get("input", {})

                    print(f"Executing tool: {tool_name} for source: {tool_input.get('source_id', 'unknown')}")

                    # Execute tool
                    result = self._execute_tool(project_id, tool_name, tool_input)

                    # Add tool result as user message
                    message_service.add_tool_result_message(
                        project_id=project_id,
                        chat_id=chat_id,
                        tool_use_id=tool_id,
                        result=result
                    )

                # Rebuild messages and call Claude again
                api_messages = message_service.build_api_messages(project_id, chat_id)

                response = claude_service.send_message(
                    messages=api_messages,
                    system_prompt=system_prompt,
                    model=prompt_config.get("model"),
                    max_tokens=prompt_config.get("max_tokens"),
                    temperature=prompt_config.get("temperature"),
                    tools=tools,
                    project_id=project_id
                )

                # Log the follow-up API call
                self._log_api_call(
                    project_id=project_id,
                    chat_id=chat_id,
                    system_prompt=system_prompt,
                    messages=api_messages,
                    tools=tools,
                    model=prompt_config.get("model"),
                    max_tokens=prompt_config.get("max_tokens"),
                    temperature=prompt_config.get("temperature"),
                    response=response
                )

            # Step 6: Store final text response
            final_text = claude_parsing_utils.extract_text(response)

            assistant_msg = message_service.add_assistant_message(
                project_id=project_id,
                chat_id=chat_id,
                content=final_text,
                model=response.get("model"),
                tokens=response.get("usage")
            )

        except Exception as api_error:
            # Store error message
            assistant_msg = message_service.add_assistant_message(
                project_id=project_id,
                chat_id=chat_id,
                content=f"Sorry, I encountered an error: {str(api_error)}",
                error=True
            )

        # Step 7: Sync chat index
        chat_service.sync_chat_to_index(project_id, chat_id)

        # Step 8: Auto-rename chat on first message (background task)
        # Educational Note: We check if the chat had no messages before this one.
        # The naming runs in background so it doesn't block the response.
        if chat.get("message_count", 0) == 0:
            # Submit naming task to background
            task_service.submit_task(
                "chat_naming",
                chat_id,
                self._generate_and_update_chat_title,
                project_id,
                chat_id,
                user_message_text
            )

        return user_msg, assistant_msg

    def _generate_and_update_chat_title(
        self,
        project_id: str,
        chat_id: str,
        user_message: str
    ) -> None:
        """
        Generate and update chat title in background.

        Educational Note: This runs as a background task so it doesn't
        block the main chat response. Uses AI to generate a concise title.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            user_message: The user's first message
        """
        try:
            new_title = chat_naming_service.generate_title(user_message, project_id=project_id)
            if new_title:
                chat_service.update_chat(project_id, chat_id, {"title": new_title})
                print(f"Auto-renamed chat {chat_id} to: {new_title}")
        except Exception as e:
            print(f"Error auto-naming chat {chat_id}: {e}")


# Singleton instance
main_chat_service = MainChatService()
