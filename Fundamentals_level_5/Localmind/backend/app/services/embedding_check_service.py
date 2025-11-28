"""
Embedding Check Service - Determine if a source needs vector embeddings.

Educational Note: Not all sources need embeddings. Short documents can be
included directly in the chat context. We only create embeddings for longer
documents where semantic search (RAG) is beneficial.

Decision Logic:
1. If character count > 30,000 → definitely needs embedding (skip token count)
2. If character count <= 30,000 → count actual tokens
3. If token count > 2,500 → needs embedding
4. Otherwise → use direct context injection

Why this approach?
- Token counting via API has a cost (even if small)
- 30,000 chars ≈ 7,500 tokens, well above our 2,500 threshold
- We only do precise token counting for borderline cases
"""
from typing import Tuple, Optional


# Thresholds for embedding decision
CHARACTER_THRESHOLD = 30000  # If above this, definitely needs embedding
TOKEN_THRESHOLD = 2500  # If token count above this, needs embedding


class EmbeddingCheckService:
    """
    Service for determining if a source needs vector embeddings.

    Educational Note: This service helps optimize costs by:
    - Using fast character counting for obvious cases
    - Only calling the token counting API for borderline cases
    - Providing a clear decision on whether to embed or not
    """

    def __init__(self):
        """Initialize the embedding check service."""
        pass

    def needs_embedding(
        self,
        text: str,
        character_count: Optional[int] = None
    ) -> Tuple[bool, int, str]:
        """
        Determine if text needs embedding based on length.

        Educational Note: We use a two-tier approach:
        1. Quick check: If character count is very high, skip token counting
        2. Precise check: For borderline cases, use actual token counting

        Args:
            text: The processed text content to check
            character_count: Optional pre-calculated character count

        Returns:
            Tuple of:
                - needs_embedding (bool): Whether to create embeddings
                - token_count (int): Actual or estimated token count
                - reason (str): Explanation of the decision
        """
        if not text or not text.strip():
            return False, 0, "Empty text - no embedding needed"

        # Use provided character count or calculate it
        char_count = character_count if character_count is not None else len(text)

        # Always use precise token counting (API is free)
        token_count = self._count_tokens_precise(text)

        # Quick check: If character count is high, definitely needs embedding
        if char_count > CHARACTER_THRESHOLD:
            return True, token_count, f"Character count ({char_count:,}) exceeds threshold ({CHARACTER_THRESHOLD:,}) - embedding required"

        if token_count > TOKEN_THRESHOLD:
            return True, token_count, f"Token count ({token_count:,}) exceeds threshold ({TOKEN_THRESHOLD:,}) - embedding required"
        else:
            return False, token_count, f"Token count ({token_count:,}) below threshold ({TOKEN_THRESHOLD:,}) - direct context OK"

    def _count_tokens_precise(self, text: str) -> int:
        """
        Count tokens using Claude's count_tokens API.

        Educational Note: We format the text as a system prompt + simple user
        message to get an accurate token count that reflects how it would be
        used in actual chat context.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens
        """
        from app.services.claude_service import claude_service

        # Format as it would appear in chat context
        # System prompt contains the source text, user message is minimal
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        system_prompt = text

        try:
            token_count = claude_service.count_tokens(
                messages=messages,
                system_prompt=system_prompt
            )
            return token_count
        except Exception as e:
            # Fallback to character-based estimation if API fails
            print(f"Token counting failed, using estimation: {e}")
            return len(text) // 4

    def get_thresholds(self) -> dict:
        """
        Get the current threshold values.

        Returns:
            Dict with character and token thresholds
        """
        return {
            "character_threshold": CHARACTER_THRESHOLD,
            "token_threshold": TOKEN_THRESHOLD
        }


# Singleton instance for easy import
embedding_check_service = EmbeddingCheckService()
