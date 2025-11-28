"""
Chat Naming Service - Generate concise chat titles using AI.

Educational Note: This service generates short, descriptive titles for chats
based on the first user message. It uses Claude Haiku for fast, cost-effective
naming (~$0.001 per title).

Usage:
- Called automatically when user sends first message in a new chat
- Generates 1-5 word title that captures the chat's topic
"""
from typing import Optional

from app.services.claude_service import claude_service


class ChatNamingService:
    """
    Service for generating chat titles using AI.

    Educational Note: Uses Haiku model for speed and cost efficiency.
    The title should be concise (1-5 words) and capture the essence
    of what the user is asking about.
    """

    # System prompt for chat naming
    SYSTEM_PROMPT = """You are a chat title generator. Your task is to create a short, descriptive title for a chat conversation based on the user's first message.

STRICT RULES:
1. Output ONLY the title - no quotes, no explanations, no punctuation at the end
2. Title must be 1-5 words maximum
3. Capture the main topic or intent of the message
4. Use title case (capitalize major words)
5. Be specific but concise

Examples:
- "How do I fix this bug in my Python code?" -> "Python Bug Fix"
- "Explain quantum computing to me" -> "Quantum Computing Explained"
- "What's the weather like today?" -> "Weather Today"
- "Help me write a resume" -> "Resume Writing Help"
- "Tell me about machine learning" -> "Machine Learning Overview"
"""

    def generate_title(self, first_message: str, project_id: Optional[str] = None) -> Optional[str]:
        """
        Generate a chat title based on the first user message.

        Args:
            first_message: The user's first message in the chat
            project_id: Optional project ID for cost tracking

        Returns:
            A 1-5 word title, or None if generation fails
        """
        if not first_message or not first_message.strip():
            return None

        try:
            response = claude_service.send_message(
                messages=[{"role": "user", "content": first_message}],
                system_prompt=self.SYSTEM_PROMPT,
                model="claude-haiku-4-5-20251001",
                max_tokens=10,  # Very short output
                temperature=0.3,  # Low temperature for consistency
                project_id=project_id
            )

            title = response.get("content", "").strip()

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
