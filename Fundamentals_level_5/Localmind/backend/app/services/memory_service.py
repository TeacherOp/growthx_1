"""
Memory Service - Manage user and project memory storage.

Educational Note: This service handles persistent memory storage for the chat system.
Memory is stored in two types:
- User memory: Global preferences and context that persists across all projects
- Project memory: Project-specific context that is deleted when the project is deleted

The service uses Haiku AI to intelligently merge new memory with existing memory,
keeping the content concise (max 150 tokens per memory type).
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from config import Config
from app.services.claude_service import claude_service
from app.services.tool_loader import tool_loader
from app.services.message_service import message_service
from app.services.prompt_service import prompt_service


class MemoryService:
    """
    Service for managing user and project memory.

    Educational Note: Memory helps the AI maintain context across conversations.
    - User memory: name, preferences, communication style, general goals
    - Project memory: project goals, milestones, decisions, progress
    """

    def __init__(self):
        """Initialize the memory service."""
        self.data_dir = Config.DATA_DIR
        self.projects_dir = Config.PROJECTS_DIR
        self._prompt_config: Optional[Dict[str, Any]] = None
        self._tool_def: Optional[Dict[str, Any]] = None

    def _load_prompt_config(self) -> Dict[str, Any]:
        """Load the memory merge prompt configuration using prompt_service."""
        if self._prompt_config is None:
            self._prompt_config = prompt_service.get_prompt_config("memory")

            if not self._prompt_config:
                raise FileNotFoundError("Memory prompt config not found")

        return self._prompt_config

    def _load_tool_definition(self) -> Dict[str, Any]:
        """Load the save_memory tool definition."""
        if self._tool_def is None:
            self._tool_def = tool_loader.load_tool("memory_tools", "manage_memory_tool")
        return self._tool_def

    def _get_user_memory_path(self) -> Path:
        """Get the path to the user memory file."""
        return self.data_dir / "user_memory.json"

    def _get_project_memory_path(self, project_id: str) -> Path:
        """Get the path to a project's memory file."""
        return self.projects_dir / project_id / "memory.json"

    def get_user_memory(self) -> Optional[str]:
        """
        Get the current user memory content.

        Returns:
            User memory string or None if no memory exists
        """
        memory_path = self._get_user_memory_path()

        if not memory_path.exists():
            return None

        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("memory")
        except Exception as e:
            print(f"Error reading user memory: {e}")
            return None

    def get_project_memory(self, project_id: str) -> Optional[str]:
        """
        Get the current project memory content.

        Args:
            project_id: The project UUID

        Returns:
            Project memory string or None if no memory exists
        """
        memory_path = self._get_project_memory_path(project_id)

        if not memory_path.exists():
            return None

        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("memory")
        except Exception as e:
            print(f"Error reading project memory: {e}")
            return None

    def _save_user_memory(self, memory: str) -> bool:
        """
        Save user memory to file.

        Args:
            memory: The memory content to save

        Returns:
            True if saved successfully
        """
        memory_path = self._get_user_memory_path()

        try:
            data = {
                "memory": memory,
                "updated_at": datetime.now().isoformat()
            }
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving user memory: {e}")
            return False

    def _save_project_memory(self, project_id: str, memory: str) -> bool:
        """
        Save project memory to file.

        Args:
            project_id: The project UUID
            memory: The memory content to save

        Returns:
            True if saved successfully
        """
        memory_path = self._get_project_memory_path(project_id)

        # Ensure project directory exists
        memory_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = {
                "memory": memory,
                "updated_at": datetime.now().isoformat()
            }
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving project memory: {e}")
            return False

    def _build_user_message(
        self,
        memory_type: str,
        current_memory: str,
        new_memory: str,
        reason: str
    ) -> str:
        """
        Build user message from prompt config template.

        Educational Note: Following the pattern from pptx_extraction_prompt.json,
        we use a template in the prompt config and fill in the variables.

        Args:
            memory_type: "user" or "project"
            current_memory: Existing memory content
            new_memory: New memory to incorporate
            reason: Why this update was triggered

        Returns:
            Formatted user message
        """
        prompt_config = self._load_prompt_config()
        template = prompt_config.get("user_message", "")

        return template.format(
            memory_type=memory_type,
            current_memory=current_memory if current_memory else "(empty - no existing memory)",
            new_memory=new_memory,
            reason=reason
        )

    def update_memory(
        self,
        memory_type: str,
        new_memory: str,
        reason: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update memory by merging new content with existing memory using AI.

        Educational Note: This method uses Haiku AI to intelligently merge
        existing memory with new memory. The AI:
        1. Receives current memory + new memory via templated user message
        2. Creates a merged, condensed version (max 150 tokens)
        3. Returns the result via the save_memory tool
        4. We use message_service to parse the tool response

        Args:
            memory_type: "user" or "project"
            new_memory: New memory content to merge
            reason: Why this memory update was triggered
            project_id: Required if memory_type is "project"

        Returns:
            Dict with success status and updated memory
        """
        # Validate inputs
        if memory_type not in ["user", "project"]:
            return {"success": False, "error": f"Invalid memory_type: {memory_type}"}

        if memory_type == "project" and not project_id:
            return {"success": False, "error": "project_id required for project memory"}

        # Get current memory
        if memory_type == "user":
            current_memory = self.get_user_memory() or ""
        else:
            current_memory = self.get_project_memory(project_id) or ""

        # Load prompt config and tool
        prompt_config = self._load_prompt_config()
        tool_def = self._load_tool_definition()

        # Build user message from template
        user_message = self._build_user_message(
            memory_type=memory_type,
            current_memory=current_memory,
            new_memory=new_memory,
            reason=reason
        )

        try:
            # Call Haiku AI with the save_memory tool
            response = claude_service.send_message(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=prompt_config.get('system_prompt'),
                model=prompt_config.get('model', 'claude-haiku-4-5-20251001'),
                max_tokens=prompt_config.get('max_tokens', 200),
                temperature=prompt_config.get('temperature', 0.1),
                tools=[tool_def],
                project_id=project_id  # Track costs for project memory
            )

            # Use message_service to parse tool calls
            tool_inputs = message_service.extract_tool_inputs(response, "save_memory")

            if not tool_inputs:
                return {
                    "success": False,
                    "error": "AI did not use save_memory tool"
                }

            # Get the first tool input (should only be one)
            tool_input = tool_inputs[0]
            merged_memory = tool_input.get("memory", "")

            if not merged_memory:
                return {
                    "success": False,
                    "error": "AI returned empty memory"
                }

            # Save the merged memory
            if memory_type == "user":
                saved = self._save_user_memory(merged_memory)
            else:
                saved = self._save_project_memory(project_id, merged_memory)

            if saved:
                print(f"Memory updated ({memory_type}): {merged_memory[:50]}...")
                return {
                    "success": True,
                    "memory_type": memory_type,
                    "memory": merged_memory,
                    "previous_memory": current_memory,
                    "model": response.get("model"),
                    "usage": response.get("usage")
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to save memory to file"
                }

        except Exception as e:
            print(f"Error updating memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def delete_project_memory(self, project_id: str) -> bool:
        """
        Delete project memory file.

        Educational Note: Called when a project is deleted to clean up
        associated memory.

        Args:
            project_id: The project UUID

        Returns:
            True if deleted or didn't exist
        """
        memory_path = self._get_project_memory_path(project_id)

        try:
            if memory_path.exists():
                memory_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting project memory: {e}")
            return False


# Singleton instance
memory_service = MemoryService()
