"""
Message Service - Handles message persistence and retrieval for chat conversations.

Educational Note: This is a pure CRUD service for chat messages.
It handles storing and retrieving messages, building message arrays for API calls.

Key Responsibilities:
- Store messages to chat JSON files
- Retrieve message history
- Build message arrays for Claude API calls
- Support different message types (user, assistant, tool_result)

For parsing Claude API responses (tool_use blocks, content extraction),
see utils/claude_parsing_utils.py
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from config import Config
from app.utils import claude_parsing_utils


class MessageService:
    """
    Service class for message persistence and context management.

    Educational Note: Messages are stored in individual chat JSON files.
    This service handles the format conversion between storage and API.
    """

    def __init__(self):
        """Initialize the message service."""
        self.projects_dir = Config.PROJECTS_DIR

    def _get_chat_file(self, project_id: str, chat_id: str) -> Path:
        """Get the path to a chat's JSON file."""
        return self.projects_dir / project_id / "chats" / f"{chat_id}.json"

    def _load_chat_data(self, project_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Load chat data from file.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID

        Returns:
            Chat data dict or None if not found
        """
        chat_file = self._get_chat_file(project_id, chat_id)

        if not chat_file.exists():
            return None

        try:
            with open(chat_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None

    def _save_chat_data(self, project_id: str, chat_id: str, data: Dict[str, Any]) -> bool:
        """
        Save chat data to file.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            data: Chat data to save

        Returns:
            True if successful
        """
        chat_file = self._get_chat_file(project_id, chat_id)

        try:
            with open(chat_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except IOError:
            return False

    def get_messages(self, project_id: str, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages from a chat.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID

        Returns:
            List of message dicts
        """
        chat_data = self._load_chat_data(project_id, chat_id)
        if not chat_data:
            return []
        return chat_data.get("messages", [])

    def add_message(
        self,
        project_id: str,
        chat_id: str,
        role: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a message to a chat.

        Educational Note: This handles different content types:
        - String content for simple user/assistant messages
        - List content for tool_use/tool_result blocks

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            role: Message role ('user' or 'assistant')
            content: Message content (string or list of content blocks)
            metadata: Optional metadata (model, tokens, error, etc.)

        Returns:
            The created message dict, or None if chat not found
        """
        chat_data = self._load_chat_data(project_id, chat_id)
        if not chat_data:
            return None

        # Create message
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        # Add optional metadata
        if metadata:
            message.update(metadata)

        # Append to messages
        chat_data["messages"].append(message)
        chat_data["updated_at"] = datetime.now().isoformat()
        chat_data["message_count"] = len(chat_data["messages"])

        # Save
        self._save_chat_data(project_id, chat_id, chat_data)

        return message

    def add_user_message(
        self,
        project_id: str,
        chat_id: str,
        content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Add a user message to a chat.

        Educational Note: Convenience method for the common case of
        adding a simple text message from the user.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            content: The user's message text

        Returns:
            The created message dict
        """
        return self.add_message(project_id, chat_id, "user", content)

    def add_assistant_message(
        self,
        project_id: str,
        chat_id: str,
        content: str,
        model: Optional[str] = None,
        tokens: Optional[Dict[str, int]] = None,
        error: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Add an assistant message to a chat.

        Educational Note: Includes metadata about the model and token usage
        for tracking and debugging purposes.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            content: The assistant's response text
            model: Model used to generate response
            tokens: Token usage dict with 'input' and 'output'
            error: Whether this is an error message

        Returns:
            The created message dict
        """
        metadata = {}
        if model:
            metadata["model"] = model
        if tokens:
            metadata["tokens"] = tokens
        if error:
            metadata["error"] = True

        return self.add_message(project_id, chat_id, "assistant", content, metadata)

    def add_tool_result_message(
        self,
        project_id: str,
        chat_id: str,
        tool_use_id: str,
        result: Any,
        is_error: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Add a tool result message to a chat.

        Educational Note: After Claude requests a tool use, we need to
        send back the result. This is a user message with tool_result content.
        Uses claude_parsing_utils for content block building.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            tool_use_id: The ID from the tool_use block
            result: The tool execution result
            is_error: Whether the tool execution failed

        Returns:
            The created message dict
        """
        # Use claude_parsing_utils to build the tool_result content block
        content = claude_parsing_utils.build_single_tool_result(
            tool_use_id=tool_use_id,
            result=str(result) if not isinstance(result, str) else result,
            is_error=is_error
        )
        return self.add_message(project_id, chat_id, "user", content)

    def build_api_messages(
        self,
        project_id: str,
        chat_id: str,
        include_pending: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Build message array for Claude API call.

        Educational Note: The Claude API expects messages in a specific format.
        This method converts stored messages to the API format, optionally
        including a pending message that hasn't been saved yet.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            include_pending: Optional message to include at the end

        Returns:
            List of message dicts ready for Claude API
        """
        messages = self.get_messages(project_id, chat_id)

        # Convert to API format
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add pending message if provided
        if include_pending:
            api_messages.append({
                "role": include_pending["role"],
                "content": include_pending["content"]
            })

        return api_messages

    def build_context_from_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Build API message array from a list of messages.

        Educational Note: This is useful for subagents or other flows
        that don't use stored chat messages but need to build context.

        Args:
            messages: List of message dicts

        Returns:
            List of message dicts ready for Claude API
        """
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

    def update_chat_metadata(
        self,
        project_id: str,
        chat_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update chat metadata (not messages).

        Educational Note: Used for updating things like title, source_references,
        sub_agents metadata without modifying messages.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            updates: Dict of fields to update

        Returns:
            True if successful
        """
        chat_data = self._load_chat_data(project_id, chat_id)
        if not chat_data:
            return False

        # Update fields
        for key, value in updates.items():
            if key != "messages":  # Don't allow message updates via this method
                chat_data[key] = value

        chat_data["updated_at"] = datetime.now().isoformat()

        return self._save_chat_data(project_id, chat_id, chat_data)


# Singleton instance for easy import
message_service = MessageService()
