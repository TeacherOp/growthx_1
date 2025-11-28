"""
Chat Service - CRUD operations for chat entities.

Educational Note: This service manages chat entity lifecycle within projects.
It handles creating, listing, getting, updating, and deleting chats.

Separation of Concerns:
- chat_service.py: Chat CRUD (this file)
- claude_service.py: Claude API interactions
- message_service.py: Message persistence
- prompt_service.py: Prompt management
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from config import Config


class ChatService:
    """
    Service class for chat entity management.

    Educational Note: A chat is a conversation container within a project.
    It has metadata (title, timestamps) and holds messages.
    """

    def __init__(self):
        """Initialize the chat service."""
        self.projects_dir = Config.PROJECTS_DIR

    def _get_chats_dir(self, project_id: str) -> Path:
        """Get the chats directory for a project."""
        chats_dir = self.projects_dir / project_id / "chats"
        chats_dir.mkdir(exist_ok=True, parents=True)
        return chats_dir

    def _get_index_file(self, project_id: str) -> Path:
        """Get the chats index file path."""
        return self._get_chats_dir(project_id) / "chats_index.json"

    def _get_chat_file(self, project_id: str, chat_id: str) -> Path:
        """Get a specific chat's file path."""
        return self._get_chats_dir(project_id) / f"{chat_id}.json"

    def _load_index(self, project_id: str) -> Dict[str, Any]:
        """
        Load the chats index for a project.

        Educational Note: The index provides quick access to chat metadata
        without loading full chat files with all messages.
        """
        index_file = self._get_index_file(project_id)

        if not index_file.exists():
            # Initialize empty index
            initial_index = {
                "project_id": project_id,
                "chats": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_index(project_id, initial_index)
            return initial_index

        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Reinitialize if corrupted
            initial_index = {
                "project_id": project_id,
                "chats": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_index(project_id, initial_index)
            return initial_index

    def _save_index(self, project_id: str, index_data: Dict[str, Any]) -> bool:
        """Save the chats index."""
        index_data["last_updated"] = datetime.now().isoformat()
        index_file = self._get_index_file(project_id)

        try:
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
            return True
        except IOError:
            return False

    def list_chats(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all chats for a project.

        Educational Note: Returns metadata only (not full messages) for
        efficient loading of chat lists in the UI.

        Args:
            project_id: The project UUID

        Returns:
            List of chat metadata, sorted by most recent first
        """
        index = self._load_index(project_id)

        # Sort by updated_at, most recent first
        chats = sorted(
            index["chats"],
            key=lambda c: c.get("updated_at", c["created_at"]),
            reverse=True
        )
        return chats

    def create_chat(self, project_id: str, title: str = "New Chat") -> Dict[str, Any]:
        """
        Create a new chat in a project.

        Educational Note: Initializes an empty conversation with metadata.
        Messages are added separately via message_service.

        Args:
            project_id: The project UUID
            title: Initial chat title

        Returns:
            Created chat metadata
        """
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Chat metadata for index
        chat_metadata = {
            "id": chat_id,
            "title": title,
            "created_at": timestamp,
            "updated_at": timestamp,
            "message_count": 0
        }

        # Full chat data for file
        chat_data = {
            "id": chat_id,
            "project_id": project_id,
            "title": title,
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": [],
            "metadata": {
                "source_references": [],
                "sub_agents": []
            },
            "message_count": 0
        }

        # Save chat file
        chat_file = self._get_chat_file(project_id, chat_id)
        with open(chat_file, 'w') as f:
            json.dump(chat_data, f, indent=2)

        # Update index
        index = self._load_index(project_id)
        index["chats"].append(chat_metadata)
        self._save_index(project_id, index)

        print(f"Created chat: {title} (ID: {chat_id})")

        return chat_metadata

    def get_chat(self, project_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full chat data including messages.

        Educational Note: Filters out tool_use and tool_result messages
        from the response. These are internal messages used in the tool
        chain and shouldn't be displayed to users.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID

        Returns:
            Full chat data or None if not found
        """
        chat_file = self._get_chat_file(project_id, chat_id)

        if not chat_file.exists():
            return None

        try:
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)

            # Filter out tool_use and tool_result messages for display
            # These have content as arrays instead of strings
            chat_data["messages"] = [
                msg for msg in chat_data.get("messages", [])
                if isinstance(msg.get("content"), str)
            ]

            return chat_data
        except json.JSONDecodeError:
            print(f"Warning: Corrupted chat file: {chat_id}")
            return None

    def get_chat_metadata(self, project_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chat metadata only (without messages).

        Educational Note: Useful for quick lookups without loading
        the full message history.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID

        Returns:
            Chat metadata or None if not found
        """
        index = self._load_index(project_id)

        for chat in index["chats"]:
            if chat["id"] == chat_id:
                return chat
        return None

    def update_chat(
        self,
        project_id: str,
        chat_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update chat metadata.

        Educational Note: Currently supports updating title.
        Messages are updated via message_service.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID
            updates: Dict of fields to update (e.g., {"title": "New Title"})

        Returns:
            Updated chat metadata or None if not found
        """
        chat_file = self._get_chat_file(project_id, chat_id)

        if not chat_file.exists():
            return None

        try:
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)

            # Apply updates
            for key, value in updates.items():
                if key in ["title"]:  # Allowed updates
                    chat_data[key] = value

            chat_data["updated_at"] = datetime.now().isoformat()

            # Save chat file
            with open(chat_file, 'w') as f:
                json.dump(chat_data, f, indent=2)

            # Update index
            self._update_index_entry(project_id, chat_id, chat_data)

            return {
                "id": chat_data["id"],
                "title": chat_data["title"],
                "created_at": chat_data["created_at"],
                "updated_at": chat_data["updated_at"],
                "message_count": len(chat_data["messages"])
            }

        except (json.JSONDecodeError, IOError):
            return None

    def delete_chat(self, project_id: str, chat_id: str) -> bool:
        """
        Delete a chat and all its messages.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID

        Returns:
            True if deleted, False if not found
        """
        chat_file = self._get_chat_file(project_id, chat_id)

        if not chat_file.exists():
            return False

        # Delete chat file
        chat_file.unlink()

        # Remove from index
        index = self._load_index(project_id)
        index["chats"] = [c for c in index["chats"] if c["id"] != chat_id]
        self._save_index(project_id, index)

        print(f"Deleted chat: {chat_id}")
        return True

    def _update_index_entry(
        self,
        project_id: str,
        chat_id: str,
        chat_data: Dict[str, Any]
    ):
        """Update a chat's entry in the index."""
        index = self._load_index(project_id)

        for i, chat in enumerate(index["chats"]):
            if chat["id"] == chat_id:
                index["chats"][i] = {
                    "id": chat_data["id"],
                    "title": chat_data["title"],
                    "created_at": chat_data["created_at"],
                    "updated_at": chat_data["updated_at"],
                    "message_count": len(chat_data["messages"])
                }
                break

        self._save_index(project_id, index)

    def sync_chat_to_index(self, project_id: str, chat_id: str) -> bool:
        """
        Sync a chat's metadata to the index.

        Educational Note: Called after message_service adds messages
        to ensure the index stays up to date.

        Args:
            project_id: The project UUID
            chat_id: The chat UUID

        Returns:
            True if successful
        """
        chat_data = self.get_chat(project_id, chat_id)
        if not chat_data:
            return False

        self._update_index_entry(project_id, chat_id, chat_data)
        return True


# Singleton instance for easy import
chat_service = ChatService()
