"""
Prompt Config - Manages system prompts for AI interactions.

Educational Note: This module handles loading, storing, and retrieving
prompts used in AI conversations. Projects can have custom prompts or
fall back to the global default.

Prompt Config Structure (consistent across all prompt files):
{
    "version": "2.0",
    "name": "prompt_name",
    "description": "What this prompt is for",
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "temperature": 0.7,
    "system_prompt": "The actual prompt text...",
    "created_at": "...",
    "updated_at": "..."
}

Prompt Hierarchy:
1. Project custom prompt (if set)
2. Global default prompt (fallback)
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

from config import Config


class PromptLoader:
    """
    Loader class for managing system prompts.

    Educational Note: Prompts define how the AI behaves. Different projects
    might need different prompts based on their use case (research, coding,
    learning, etc.).
    """

    def __init__(self):
        """Initialize the prompt service."""
        self.prompts_dir = Config.DATA_DIR / "prompts"
        self.projects_dir = Config.PROJECTS_DIR

        # Ensure prompts directory exists
        self.prompts_dir.mkdir(exist_ok=True, parents=True)

    def get_default_prompt_config(self) -> Dict[str, Any]:
        """
        Load the full default prompt configuration.

        Educational Note: Returns the complete prompt config including
        model, max_tokens, temperature, and system_prompt. This allows
        services to use consistent settings from a single source.

        Returns:
            Dict with all prompt config fields
        """
        default_prompt_file = self.prompts_dir / "default_prompt.json"

        with open(default_prompt_file, 'r') as f:
            prompt_data = json.load(f)

            # Handle legacy format where "prompt" was used instead of "system_prompt"
            if "prompt" in prompt_data and "system_prompt" not in prompt_data:
                prompt_data["system_prompt"] = prompt_data.pop("prompt")

            return prompt_data

    def get_default_prompt(self) -> str:
        """
        Load the global default system prompt text.

        Educational Note: This is used when projects don't have custom prompts.
        It provides a baseline behavior for the AI assistant.

        Returns:
            The default system prompt text
        """
        config = self.get_default_prompt_config()
        return config.get("system_prompt", "")

    def get_project_prompt(self, project_id: str) -> str:
        """
        Get the prompt for a specific project.

        Educational Note: First checks for a custom prompt in project settings,
        then falls back to the global default.

        Args:
            project_id: The project UUID

        Returns:
            The project's system prompt (custom or default)
        """
        project_file = self.projects_dir / f"{project_id}.json"

        try:
            with open(project_file, 'r') as f:
                project_data = json.load(f)
                custom_prompt = project_data.get("settings", {}).get("custom_prompt")

                if custom_prompt:
                    return custom_prompt
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Return default if no custom prompt
        return self.get_default_prompt()

    def get_project_prompt_config(self, project_id: str) -> Dict[str, Any]:
        """
        Get the full prompt config for a specific project.

        Educational Note: Returns the default config but with custom prompt
        if the project has one. This ensures model/max_tokens/temperature
        come from the default config even when using custom prompts.

        Args:
            project_id: The project UUID

        Returns:
            Dict with all prompt config fields
        """
        config = self.get_default_prompt_config()

        # Check for custom prompt override
        project_file = self.projects_dir / f"{project_id}.json"

        try:
            with open(project_file, 'r') as f:
                project_data = json.load(f)
                custom_prompt = project_data.get("settings", {}).get("custom_prompt")

                if custom_prompt:
                    config["system_prompt"] = custom_prompt
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        return config

    def update_project_prompt(self, project_id: str, prompt: Optional[str]) -> bool:
        """
        Update a project's custom prompt.

        Educational Note: Setting prompt to None removes the custom prompt
        and reverts to the default.

        Args:
            project_id: The project UUID
            prompt: New custom prompt, or None to reset to default

        Returns:
            True if successful, False if project not found
        """
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            return False

        try:
            with open(project_file, 'r') as f:
                project_data = json.load(f)

            # Ensure settings dict exists
            if "settings" not in project_data:
                project_data["settings"] = {}

            # Update or remove custom prompt
            if prompt:
                project_data["settings"]["custom_prompt"] = prompt
            else:
                # Remove custom prompt to use default
                project_data["settings"].pop("custom_prompt", None)

            # Save updated project
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)

            return True

        except (json.JSONDecodeError, IOError):
            return False

    def save_default_prompt(self, prompt: str) -> bool:
        """
        Update the global default prompt.

        Educational Note: This affects all projects that don't have
        custom prompts. Use with caution.

        Args:
            prompt: New default prompt text

        Returns:
            True if successful
        """
        default_prompt_file = self.prompts_dir / "default_prompt.json"

        try:
            prompt_data = {"prompt": prompt}
            with open(default_prompt_file, 'w') as f:
                json.dump(prompt_data, f, indent=2)
            return True
        except IOError:
            return False

    def get_agent_prompt(self, agent_name: str) -> Optional[str]:
        """
        Load a prompt for a specific agent.

        Educational Note: Agents (like web_agent, pdf_agent, etc.) have
        their own specialized prompts stored in data/prompts/{agent_name}_prompt.json

        Args:
            agent_name: Name of the agent (e.g., "web_agent")

        Returns:
            The agent's system prompt, or None if not found
        """
        prompt_file = self.prompts_dir / f"{agent_name}_prompt.json"

        try:
            with open(prompt_file, 'r') as f:
                prompt_data = json.load(f)
                # Look for system_prompt first (new format), then prompt (legacy)
                return prompt_data.get("system_prompt") or prompt_data.get("prompt")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def get_prompt_config(self, prompt_name: str) -> Optional[Dict[str, Any]]:
        """
        Load full prompt configuration by name.

        Educational Note: Loads the complete prompt config including
        model, max_tokens, temperature, system_prompt, and user_message.
        Used by services like memory_service, summary_service for
        specialized AI tasks.

        Args:
            prompt_name: Name of the prompt file (without _prompt.json suffix)
                        e.g., "memory" loads "memory_prompt.json"

        Returns:
            Full prompt config dict, or None if not found
        """
        prompt_file = self.prompts_dir / f"{prompt_name}_prompt.json"

        try:
            with open(prompt_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def list_all_prompts(self) -> list[Dict[str, Any]]:
        """
        List all prompt configurations from the prompts directory.

        Educational Note: This dynamically reads all *_prompt.json files
        from the prompts directory, making it easy to add new prompts
        without code changes.

        Returns:
            List of prompt config dicts with all fields
        """
        prompts = []

        # Get all prompt JSON files
        prompt_files = sorted(self.prompts_dir.glob("*_prompt.json"))

        for prompt_file in prompt_files:
            try:
                with open(prompt_file, 'r') as f:
                    prompt_data = json.load(f)

                    # Handle legacy format where "prompt" was used instead of "system_prompt"
                    if "prompt" in prompt_data and "system_prompt" not in prompt_data:
                        prompt_data["system_prompt"] = prompt_data.pop("prompt")

                    # Add filename for reference
                    prompt_data["filename"] = prompt_file.name

                    prompts.append(prompt_data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading prompt {prompt_file}: {e}")
                continue

        return prompts


# Singleton instance for easy import
prompt_loader = PromptLoader()
