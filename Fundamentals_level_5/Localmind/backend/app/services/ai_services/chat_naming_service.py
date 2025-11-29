"""
Chat Naming Service - Generate concise chat titles using AI.

Educational Note: This service generates short, descriptive titles for chats
based on the first user message. It uses Claude Haiku for fast, cost-effective
naming (~$0.001 per title).

Usage:
- Called automatically when user sends first message in a new chat
- Generates 1-5 word title that captures the chat's topic
- Prompt config loaded from data/prompts/chat_naming_prompt.json
"""
from typing import Optional

from app.services.integrations.claude import claude_service
from app.config import prompt_loader
from app.utils import claude_parsing_utils


class ChatNamingService:
    """
    Service for generating chat titles using AI.

    Educational Note: Uses Haiku model for speed and cost efficiency.
    The title should be concise (1-5 words) and capture the essence
    of what the user is asking about.

    Prompt config is loaded from data/prompts/chat_naming_prompt.json
    to maintain consistency with other services.
    """

    def __init__(self):
        """Initialize the service with cached prompt config."""
        self._prompt_config = None

    def _get_prompt_config(self) -> dict:
        """
        Load and cache the prompt config.

        Educational Note: We cache the config to avoid reading
        the file on every title generation request.
        """
        if self._prompt_config is None:
            self._prompt_config = prompt_loader.get_prompt_config("chat_naming")
            if self._prompt_config is None:
                raise ValueError("chat_naming_prompt.json not found in data/prompts/")
        return self._prompt_config

    def generate_title(self, first_message: str, project_id: Optional[str] = None) -> Optional[str]:
        """
        Generate a chat title based on the first user message.

        Educational Note: Uses prompt config from chat_naming_prompt.json
        for model, max_tokens, temperature, and system_prompt settings.

        Args:
            first_message: The user's first message in the chat
            project_id: Optional project ID for cost tracking

        Returns:
            A 1-5 word title, or None if generation fails
        """
        if not first_message or not first_message.strip():
            return None

        try:
            # Load prompt config
            config = self._get_prompt_config()

            response = claude_service.send_message(
                messages=[{"role": "user", "content": first_message}],
                system_prompt=config.get("system_prompt", ""),
                model=config.get("model"),
                max_tokens=config.get("max_tokens"),
                temperature=config.get("temperature"),
                project_id=project_id
            )

            # Use claude_parsing_utils to extract text from response
            title = claude_parsing_utils.extract_text(response).strip()

            if not title:
                return None

            # Clean up: remove quotes if present, limit words
            title = title.strip('"\'')
            words = title.split()

            # Enforce 1-5 word limit
            if len(words) > 5:
                title = " ".join(words[:5])

            return title

        except Exception as e:
            print(f"Error generating chat title: {e}")
            return None


# Singleton instance
chat_naming_service = ChatNamingService()
