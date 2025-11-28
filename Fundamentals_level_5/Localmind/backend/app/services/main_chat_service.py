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
from app.services.chat_service import chat_service
from app.services.claude_service import claude_service
from app.services.message_service import message_service
from app.services.prompt_service import prompt_service
from app.services.source_context_service import source_context_service
from app.services.source_search_executor import source_search_executor
from app.services.tool_loader import tool_loader
from app.services.chat_naming_service import chat_naming_service
from app.services.task_service import task_service


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
        self._tool_definition = None
        self.projects_dir = Config.PROJECTS_DIR

    def _get_tool(self) -> Dict[str, Any]:
        """Load the search_sources tool definition (cached)."""
        if self._tool_definition is None:
            self._tool_definition = tool_loader.load_tool("chat_tools", "source_search_tool")
        return self._tool_definition

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
                "content_blocks": self._serialize_content_blocks(
                    response.get("content_blocks", [])
                )
            }

        log_file = logs_dir / f"api_{call_number}.json"

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"Logged API call {call_number} to: {log_file}")

    def _build_system_prompt(self, project_id: str, base_prompt: str) -> str:
        """
        Build system prompt with source context appended.

        Educational Note: Source context is rebuilt on every message
        to reflect current state (active/inactive sources).
        """
        source_context = source_context_service.build_source_context(project_id)
        if source_context:
            return base_prompt + "\n" + source_context
        return base_prompt

    def _execute_tool(self, project_id: str, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool and return result string.

        Educational Note: Routes tool calls to appropriate executor.
        Currently only search_sources, but extensible for future tools.
        """
        if tool_name == "search_sources":
            result = source_search_executor.execute(
                project_id=project_id,
                source_id=tool_input.get("source_id", ""),
                query=tool_input.get("query")
            )
            if result.get("success"):
                return result.get("content", "No content found")
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        else:
            return f"Unknown tool: {tool_name}"

    def _get_text_content(self, response: Dict[str, Any]) -> str:
        """
        Extract text content from Claude response.

        Educational Note: Response content can be string or list of blocks.
        We extract only the text portions for storing as assistant message.
        """
        content = response.get("content", [])

        if isinstance(content, str):
            return content

        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        return "\n".join(text_parts)

    def _serialize_content_blocks(self, content_blocks: list) -> list:
        """
        Convert Anthropic content blocks to JSON-serializable format.

        Educational Note: Claude API returns content blocks as Anthropic objects.
        For storing in JSON, we convert them to dicts.
        """
        serialized = []
        for block in content_blocks:
            if hasattr(block, 'type'):
                if block.type == "text":
                    serialized.append({
                        "type": "text",
                        "text": block.text
                    })
                elif block.type == "tool_use":
                    serialized.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            elif isinstance(block, dict):
                serialized.append(block)
        return serialized

    def _has_tool_use(self, response: Dict[str, Any]) -> bool:
        """Check if response contains tool_use blocks."""
        return response.get("stop_reason") == "tool_use"

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
        prompt_config = prompt_service.get_project_prompt_config(project_id)
        base_prompt = prompt_config.get("system_prompt", "")
        system_prompt = self._build_system_prompt(project_id, base_prompt)

        # Step 3: Check if we have active sources (determines if we include tools)
        active_sources = source_context_service.get_active_sources(project_id)
        tools = [self._get_tool()] if active_sources else None

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
            iteration = 0
            while self._has_tool_use(response) and iteration < self.MAX_TOOL_ITERATIONS:
                iteration += 1

                # Get tool calls from response
                tool_calls = message_service.parse_tool_calls(response)

                if not tool_calls:
                    break

                # First, store the assistant's tool_use response
                # Educational Note: The message chain must be:
                # user -> assistant (tool_use) -> user (tool_result) -> assistant
                # We must store the tool_use response before the tool_result
                serialized_content = self._serialize_content_blocks(
                    response.get("content_blocks", [])
                )
                message_service.add_message(
                    project_id=project_id,
                    chat_id=chat_id,
                    role="assistant",
                    content=serialized_content
                )

                # Execute each tool and add results
                for tool_call in tool_calls:
                    tool_id = tool_call.get("id")
                    tool_name = tool_call.get("name")
                    tool_input = tool_call.get("input", {})

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
            final_text = self._get_text_content(response)

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
